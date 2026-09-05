import json
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from filegit.cli.main import app as typer_app
from filegit.cli.studio_server import app as fastapi_app

runner = CliRunner()
client = TestClient(fastapi_app)


def test_phase3_dashboard_and_traces():
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)

        try:
            repo_dir = Path(d)
            keys_dir = repo_dir / ".filegit_keys"

            # Setup repo and keys
            runner.invoke(typer_app, ["init", "--repo-path", str(repo_dir)])
            runner.invoke(typer_app, ["keygen", "--key-dir", str(keys_dir)])

            # Create a policy
            policy_file = repo_dir / "policies" / "security.md"
            policy_file.parent.mkdir(parents=True, exist_ok=True)
            policy_file.write_text("No eval.")

            # Pack using the API (Studio)
            os.environ["FILEGIT_PRIVATE_KEY"] = (
                (keys_dir / "private.pem").read_text().strip()
            )

            # Test GET /api/policies
            response = client.get("/api/policies")
            assert response.status_code == 200
            assert len(response.json()["policies"]) == 1
            assert response.json()["policies"][0]["content"] == "No eval."

            # Test POST /api/pack
            response = client.post("/api/pack")
            assert response.status_code == 200
            bundle_id = response.json()["manifest"]["id"]

            # Test POST /api/pack missing key
            del os.environ["FILEGIT_PRIVATE_KEY"]
            response_fail = client.post("/api/pack")
            assert response_fail.status_code == 400

            # Put key back for traces
            os.environ["FILEGIT_PRIVATE_KEY"] = (
                (keys_dir / "private.pem").read_text().strip()
            )

            # Record an execution trace with error to cover branch
            runner.invoke(
                typer_app,
                [
                    "trace",
                    "record",
                    "--prompt",
                    "err",
                    "--action",
                    "err",
                    "--description",
                    "err",
                ],
                env={"FILEGIT_PRIVATE_KEY": ""},
            )

            res = runner.invoke(
                typer_app,
                [
                    "trace",
                    "record",
                    "--prompt",
                    "Write a function",
                    "--action",
                    "file_edit",
                    "--description",
                    "Wrote function",
                ],
            )
            assert res.exit_code == 0

            # Record a second action to test append
            res = runner.invoke(
                typer_app,
                [
                    "trace",
                    "record",
                    "--prompt",
                    "Write a function",
                    "--action",
                    "test_run",
                    "--description",
                    "Passed",
                ],
            )
            assert res.exit_code == 0

            # Seal the trace
            res = runner.invoke(
                typer_app,
                ["trace", "seal", "--agent-id", "test-agent", "--bundle-id", bundle_id],
            )
            if res.exit_code != 0:
                print("SEAL ERROR OUTPUT:", res.stdout)
            assert res.exit_code == 0

            # Test sealing a missing trace
            res = runner.invoke(
                typer_app,
                [
                    "trace",
                    "seal",
                    "--agent-id",
                    "nonexistent",
                    "--bundle-id",
                    bundle_id,
                ],
            )
            assert res.exit_code != 0

            # Test studio command (mock uvicorn.run)
            from unittest.mock import patch

            with patch("uvicorn.run") as mock_run:
                runner.invoke(typer_app, ["studio"])
                mock_run.assert_called_once()

            # Verify the repo WITH the trace
            res = runner.invoke(typer_app, ["verify", "--require-trace"])
            assert res.exit_code == 0

            # Tamper the trace and verify it fails
            trace_files = list((repo_dir / ".filegit" / "traces").glob("trace-*.json"))
            assert len(trace_files) == 1
            trace_path = trace_files[0]

            # Test missing manifest
            manifest_path = repo_dir / ".filegit" / "manifest.json"
            manifest_data = manifest_path.read_text()
            manifest_path.unlink()
            res = runner.invoke(typer_app, ["verify", "--require-trace"])
            assert res.exit_code != 0
            manifest_path.write_text(manifest_data)

            # Tamper signature
            trace_data = json.loads(trace_path.read_text())
            trace_data["prompt"] = "Hacked prompt"
            trace_path.write_text(json.dumps(trace_data))

            res = runner.invoke(typer_app, ["verify", "--require-trace"])
            assert res.exit_code == 1  # Should fail due to signature mismatch

        finally:
            os.chdir(original_cwd)
