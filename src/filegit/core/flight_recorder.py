import os
from pathlib import Path
from datetime import datetime, timezone
import json

from filegit.domain.models import ExecutionTrace, TraceAction, Signature
from filegit.core.use_cases import FileGitUseCases

class FlightRecorder:
    def __init__(self, use_cases: FileGitUseCases):
        self.use_cases = use_cases

    def record_action(self, repo_path: Path, prompt: str, action_type: str, description: str):
        """Append an action to the current working trace."""
        trace_path = repo_path / ".filegit" / "traces" / "current_trace.json"
        
        if not trace_path.parent.exists():
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            
        trace_data = {
            "prompt": prompt,
            "actions": []
        }
        
        if trace_path.exists():
            try:
                trace_data = json.loads(self.use_cases.fs.read_text(trace_path))
            except json.JSONDecodeError:
                pass
                
        trace_data["actions"].append({
            "action_type": action_type,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        self.use_cases.fs.write_text(trace_path, json.dumps(trace_data, indent=2))

    def seal_trace(self, repo_path: Path, agent_id: str, bundle_id: str) -> ExecutionTrace:
        """Seal and sign the current trace."""
        trace_path = repo_path / ".filegit" / "traces" / "current_trace.json"
        
        if not trace_path.exists():
            raise FileNotFoundError("No active trace found to seal.")
            
        trace_data = json.loads(self.use_cases.fs.read_text(trace_path))
        
        actions = []
        for a in trace_data.get("actions", []):
            actions.append(TraceAction(**a))
            
        trace = ExecutionTrace(
            trace_id=f"trace-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            agent_id=agent_id,
            prompt=trace_data.get("prompt", ""),
            actions=actions,
            bundle_id=bundle_id
        )
        
        # Sign the trace using the same private key mechanism
        import os as builtin_os
        import base64
        priv_key_b64 = builtin_os.environ.get("FILEGIT_PRIVATE_KEY")
        if not priv_key_b64:
            raise ValueError("FILEGIT_PRIVATE_KEY is not set.")
            
        key_bytes = base64.b64decode(priv_key_b64)
        
        signature_b58 = self.use_cases.crypto.sign(key_bytes, trace.to_signable_bytes())
        pub_key = self.use_cases.crypto.get_public_key(key_bytes)
        
        trace.signature = Signature(
            key_id=f"did:filegit:{base64.b64encode(pub_key).decode('utf-8')[:16]}#keys-1",
            signature=signature_b58
        )
        
        sealed_path = repo_path / ".filegit" / "traces" / f"{trace.trace_id}.json"
        self.use_cases.fs.write_text(sealed_path, trace.model_dump_json(indent=2))
        
        # Remove the temporary current trace
        trace_path.unlink(missing_ok=True)
        
        return trace
