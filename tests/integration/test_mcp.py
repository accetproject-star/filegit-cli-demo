import pytest
import os
import tempfile
from pathlib import Path
from filegit.cli.mcp_server import read_policy, verify_compliance
from filegit.cli.main import app as typer_app
from typer.testing import CliRunner

runner = CliRunner()

def test_mcp_handlers():
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        
        try:
            repo_dir = Path(d)
            keys_dir = repo_dir / ".filegit_keys"
            
            # Setup a basic filegit repo
            runner.invoke(typer_app, ["init", "--repo-path", str(repo_dir)])
            runner.invoke(typer_app, ["keygen", "--key-dir", str(keys_dir)])
            
            policy_file = repo_dir / "policies" / "security.md"
            policy_file.write_text("No secrets.")
            
            os.environ["FILEGIT_PRIVATE_KEY"] = (keys_dir / "private.pem").read_text().strip()
            runner.invoke(typer_app, ["pack", "--repo-path", str(repo_dir)])
            
            # Test read_policy
            content = read_policy("security")
            assert content == "No secrets."
            
            # Test verify_compliance (success)
            tool_res = verify_compliance()
            assert "VERIFIED" in tool_res
            
            # Test verify_compliance (tampered)
            policy_file.write_text("Secrets are ok.")
            tool_res = verify_compliance()
            assert "BLOCK" in tool_res
            
            # Test error paths
            with pytest.raises(ValueError):
                read_policy("nonexistent")
                
        finally:
            os.chdir(original_cwd)
