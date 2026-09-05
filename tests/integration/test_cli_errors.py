import os
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from filegit.cli.main import app

runner = CliRunner()


def test_pack_without_key():
    with tempfile.TemporaryDirectory() as d:
        repo_dir = Path(d)
        if "FILEGIT_PRIVATE_KEY" in os.environ:
            del os.environ["FILEGIT_PRIVATE_KEY"]

        result = runner.invoke(app, ["pack", "--repo-path", str(repo_dir)])
        assert result.exit_code == 1
        assert "Private key not provided" in result.stdout


def test_pack_with_invalid_key_path():
    with tempfile.TemporaryDirectory() as d:
        repo_dir = Path(d)
        if "FILEGIT_PRIVATE_KEY" in os.environ:
            del os.environ["FILEGIT_PRIVATE_KEY"]

        result = runner.invoke(
            app,
            [
                "pack",
                "--repo-path",
                str(repo_dir),
                "--key-path",
                str(repo_dir / "nope.pem"),
            ],
        )
        assert result.exit_code == 1
        assert "Private key file not found" in result.stdout


def test_verify_no_manifest():
    with tempfile.TemporaryDirectory() as d:
        repo_dir = Path(d)
        result = runner.invoke(app, ["verify", "--repo-path", str(repo_dir)])
        assert result.exit_code == 1
        assert "Manifest not found" in result.stdout


def test_verify_invalid_manifest_format():
    with tempfile.TemporaryDirectory() as d:
        repo_dir = Path(d)
        fg_dir = repo_dir / ".filegit"
        fg_dir.mkdir()
        man = fg_dir / "manifest.json"
        man.write_text("invalid json")

        result = runner.invoke(app, ["verify", "--repo-path", str(repo_dir)])
        assert result.exit_code == 1
        assert "Invalid manifest format" in result.stdout
