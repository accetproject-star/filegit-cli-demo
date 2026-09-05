import os
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from filegit.cli.main import app

runner = CliRunner()


def test_full_cli_lifecycle():
    with tempfile.TemporaryDirectory() as d:
        repo_dir = Path(d)
        keys_dir = repo_dir / ".filegit_keys"

        # 1. Init
        result = runner.invoke(app, ["init", "--repo-path", str(repo_dir)])
        assert result.exit_code == 0
        assert (repo_dir / ".filegit").exists()
        assert (repo_dir / "policies").exists()

        # 2. Keygen
        result = runner.invoke(app, ["keygen", "--key-dir", str(keys_dir)])
        assert result.exit_code == 0
        assert (keys_dir / "private.pem").exists()
        assert (keys_dir / "public.pem").exists()

        # 3. Create a policy
        policy_file = repo_dir / "policies" / "security.md"
        policy_file.write_text("No hardcoded secrets.")

        # 4. Pack
        os.environ["FILEGIT_PRIVATE_KEY"] = (
            (keys_dir / "private.pem").read_text().strip()
        )
        result = runner.invoke(app, ["pack", "--repo-path", str(repo_dir)])
        assert result.exit_code == 0
        manifest_path = repo_dir / ".filegit" / "manifest.json"
        assert manifest_path.exists()

        # 5. Verify (Success)
        result = runner.invoke(app, ["verify", "--repo-path", str(repo_dir)])
        assert result.exit_code == 0
        assert "VERIFIED" in result.stdout

        # 6. Verify (Tamper test)
        policy_file.write_text("Hardcoded secrets are fine now.")
        result = runner.invoke(app, ["verify", "--repo-path", str(repo_dir)])
        assert result.exit_code == 1
        assert "Hash mismatch" in result.stdout
