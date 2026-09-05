import os
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

from filegit.domain.models import FileGitManifest, Policy, OwnerConfig, VerificationMethod, ContextBlock, Permissions, Revocation, Signature
from filegit.domain.ports import CryptoPort, HashingPort, FileSystemPort
from filegit.domain.errors import ManifestError, SignatureError, HashMismatchError, FileGitError

class FileGitUseCases:
    def __init__(self, crypto: CryptoPort, hasher: HashingPort, fs: FileSystemPort):
        self.crypto = crypto
        self.hasher = hasher
        self.fs = fs

    def init_repo(self, repo_path: Path) -> None:
        """Initializes the .filegit structure in a repository."""
        self.fs.ensure_dir(repo_path / ".filegit")
        self.fs.ensure_dir(repo_path / "policies")
        self.fs.ensure_dir(repo_path / "specs")
        self.fs.ensure_dir(repo_path / "rules")

    def generate_keys(self, key_dir: Path) -> tuple[Path, Path]:
        """Generates Ed25519 keys and saves them."""
        self.fs.ensure_dir(key_dir)
        priv_bytes, pub_bytes = self.crypto.generate_keypair()
        
        # Save to disk with proper permissions (to be handled by CLI)
        priv_path = key_dir / "private.pem"
        pub_path = key_dir / "public.pem"
        
        import base64
        self.fs.write_text(priv_path, base64.b64encode(priv_bytes).decode('utf-8'))
        self.fs.write_text(pub_path, base64.b64encode(pub_bytes).decode('utf-8'))
        
        # Enforce secure permissions 0600 on private key
        os.chmod(priv_path, 0o600)
        
        return priv_path, pub_path

    def pack(self, repo_path: Path, private_key_path: Optional[Path] = None) -> FileGitManifest:
        """Creates and signs a manifest from the current state of policies."""
        # 1. Resolve private key (Env var > --key-path)
        priv_key_str = os.environ.get("FILEGIT_PRIVATE_KEY")
        
        if not priv_key_str and private_key_path:
            if not private_key_path.exists():
                raise FileGitError(f"Private key file not found: {private_key_path}")
            # Check permissions
            st = os.stat(private_key_path)
            if bool(st.st_mode & 0o077):
                raise FileGitError(f"Private key file {private_key_path} has insecure permissions. Must be 0600.")
            priv_key_str = self.fs.read_text(private_key_path).strip()
            
        if not priv_key_str:
            raise FileGitError("Private key not provided. Set FILEGIT_PRIVATE_KEY or use --key-path.")
            
        import base64
        priv_key_bytes = base64.b64decode(priv_key_str)

        # Generate a new DID and public key for the manifest (in a real app, this is configured)
        # For MVP, we derive public key from private key, but PyNaCl signing keys already have it.
        import nacl.signing
        import nacl.encoding
        signing_key = nacl.signing.SigningKey(priv_key_bytes, encoder=nacl.encoding.RawEncoder)
        pub_key_bytes = signing_key.verify_key.encode(encoder=nacl.encoding.RawEncoder)
        pub_key_b58 = nacl.encoding.Base64Encoder.encode(pub_key_bytes).decode('utf-8')
        
        did = f"did:filegit:{pub_key_b58[:16]}"
        
        # 2. Scan and hash policies
        policies = []
        policies_dir = repo_path / "policies"
        if policies_dir.exists():
            for p_file in self.fs.iter_markdown_files(policies_dir):
                rel_path = str(p_file.relative_to(repo_path))
                f_hash = self.hasher.hash_file(p_file)
                policies.append(Policy(
                    id=f"policy-{p_file.stem}",
                    title=p_file.stem.replace('-', ' ').title(),
                    path=rel_path,
                    hash=f_hash,
                    level="high"
                ))
        
        # 3. Create Manifest
        now = datetime.now(timezone.utc)
        manifest = FileGitManifest(
            id=f"filegit-bundle-{now.strftime('%Y%m%d%H%M%S')}",
            owner=OwnerConfig(
                did=did,
                verification_method=VerificationMethod(public_key_multibase=pub_key_b58)
            ),
            created_at=now,
            valid_from=now,
            valid_until=now + timedelta(days=365),
            policies=policies
        )
        
        # 4. Sign Manifest
        signable_bytes = manifest.to_signable_bytes()
        signature_b58 = self.crypto.sign(priv_key_bytes, signable_bytes)
        
        manifest.signatures.append(Signature(
            key_id=f"{did}#keys-1",
            signature=signature_b58
        ))
        
        # 5. Write to disk
        manifest_path = repo_path / ".filegit" / "manifest.json"
        self.fs.write_text(manifest_path, manifest.model_dump_json(indent=2))
        
        return manifest

    def verify(self, repo_path: Path, manifest_path: Path, require_trace: bool = False) -> bool:
        """Verifies the integrity and signature of a manifest against local files."""
        if not manifest_path.exists():
            raise ManifestError(f"Manifest not found at {manifest_path}")
            
        manifest_json = self.fs.read_text(manifest_path)
        try:
            manifest = FileGitManifest.model_validate_json(manifest_json)
        except Exception as e:
            raise ManifestError(f"Invalid manifest format: {e}")
            
        if not manifest.signatures:
            raise SignatureError("Manifest is not signed.")
            
        # 1. Verify Signature
        sig_record = manifest.signatures[0]
        pub_key_b58 = manifest.owner.verification_method.public_key_multibase
        import base64
        pub_key_bytes = base64.b64decode(pub_key_b58)
        
        signable_bytes = manifest.to_signable_bytes()
        is_valid = self.crypto.verify(pub_key_bytes, signable_bytes, sig_record.signature)
        if not is_valid:
            raise SignatureError("Cryptographic signature verification failed. The manifest was tampered with.")
            
        # 2. Verify Hashes
        for policy in manifest.policies:
            local_path = repo_path / policy.path
            if not local_path.exists():
                raise HashMismatchError(f"Policy file missing: {policy.path}")
                
            local_hash = self.hasher.hash_file(local_path)
            if local_hash != policy.hash:
                raise HashMismatchError(f"Hash mismatch for {policy.path}. Expected {policy.hash}, got {local_hash}")
                
        # 3. Verify Execution Traces
        if require_trace:
            import json
            traces_dir = repo_path / ".filegit" / "traces"
            if not traces_dir.exists() or not any(traces_dir.glob("trace-*.json")):
                raise ManifestError("Execution trace is required but none was found.")
                
            for trace_file in traces_dir.glob("trace-*.json"):
                try:
                    trace_data = json.loads(self.fs.read_text(trace_file))
                    from filegit.domain.models import ExecutionTrace
                    trace = ExecutionTrace(**trace_data)
                    
                    if trace.bundle_id != manifest.id:
                        raise ManifestError(f"Trace {trace.trace_id} does not match current bundle.")
                        
                    if not trace.signature:
                        raise SignatureError(f"Trace {trace.trace_id} is not signed.")
                        
                    if not self.crypto.verify(pub_key_bytes, trace.to_signable_bytes(), trace.signature.signature):
                        raise SignatureError(f"Trace {trace.trace_id} has an invalid signature.")
                except Exception as e:
                    raise ManifestError(f"Invalid trace format in {trace_file.name}: {e}")
                    
        return True
