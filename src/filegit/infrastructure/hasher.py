import hashlib
from pathlib import Path
from filegit.domain.ports import HashingPort
from filegit.domain.errors import FileGitError

class SHA256Hasher(HashingPort):
    def hash_file(self, path: Path) -> str:
        """Computes SHA-256 hash of a file. Returns 'sha256:<hex>'."""
        if not path.is_file():
            raise FileGitError(f"File not found or not a file: {path}")
            
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
                
        return f"sha256:{sha256.hexdigest()}"
