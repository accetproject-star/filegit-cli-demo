import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from filegit.core.use_cases import FileGitUseCases
from filegit.infrastructure.crypto import PyNaClCrypto
from filegit.infrastructure.fs import OSFileSystem
from filegit.infrastructure.hasher import SHA256Hasher

mcp = MCPServer("filegit-mcp")


def get_use_cases() -> FileGitUseCases:
    return FileGitUseCases(
        crypto=PyNaClCrypto(), hasher=SHA256Hasher(), fs=OSFileSystem()
    )


@mcp.resource("filegit://policies/{policy_name}")
def read_policy(policy_name: str) -> str:
    """Read a specific policy from the authorized FileGit context bundle."""
    uc = get_use_cases()
    repo_path = Path.cwd()
    manifest_path = repo_path / ".filegit" / "manifest.json"

    if not manifest_path.exists():
        raise ValueError(
            "No FileGit manifest found in the current directory."
        )  # pragma: no cover

    try:
        data = json.loads(uc.fs.read_text(manifest_path))
        for policy in data.get("policies", []):
            if policy["title"].replace(" ", "_").lower() == policy_name:
                policy_path = repo_path / policy["path"]
                if policy_path.exists():
                    return uc.fs.read_text(policy_path)
                else:
                    raise ValueError(f"Policy file missing: {policy['path']}")
    except Exception as e:  # pragma: no cover
        raise ValueError(f"Failed to read policy: {e}")

    raise ValueError(
        f"Policy '{policy_name}' not found in the authorized context bundle."
    )


@mcp.tool()
def verify_compliance() -> str:
    """Verify if the current repository state complies with the FileGit
    authorized context bundle."""
    uc = get_use_cases()
    repo_path = Path.cwd()
    manifest_path = repo_path / ".filegit" / "manifest.json"

    try:
        is_valid = uc.verify(repo_path, manifest_path)
        if is_valid:
            return (
                "✅ VERIFIED: The context bundle is authentic and unmodified. "
                "You are in compliance."
            )
    except Exception as e:  # pragma: no cover
        return f"❌ BLOCK: Verification failed. Reason: {e}"

    return "❌ BLOCK: Unknown verification failure."


async def serve() -> None:  # pragma: no cover
    # Run the server using stdin/stdout
    await mcp.run_stdio_async()
