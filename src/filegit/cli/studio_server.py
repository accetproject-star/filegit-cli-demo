from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from filegit.core.use_cases import FileGitUseCases
from filegit.infrastructure.crypto import PyNaClCrypto
from filegit.infrastructure.fs import OSFileSystem
from filegit.infrastructure.hasher import SHA256Hasher

app = FastAPI(title="FileGit Studio API")

# Allow CORS for development with Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_use_cases() -> FileGitUseCases:
    return FileGitUseCases(
        crypto=PyNaClCrypto(), hasher=SHA256Hasher(), fs=OSFileSystem()
    )


class PolicyModel(BaseModel):
    title: str
    content: str
    path: str


@app.get("/api/policies")
def list_policies() -> dict[str, Any]:
    """List all markdown policies in the policies directory."""
    uc = get_use_cases()
    repo_path = Path.cwd()
    policies_dir = repo_path / "policies"

    if not policies_dir.exists():
        return {"policies": []}

    policies = []
    for policy_file in policies_dir.glob("*.md"):
        content = uc.fs.read_text(policy_file)
        policies.append(
            {
                "title": policy_file.stem.replace("-", " ").title(),
                "content": content,
                "path": f"policies/{policy_file.name}",
            }
        )

    return {"policies": policies}


@app.post("/api/pack")
def pack_policies() -> dict[str, Any]:
    """Pack and sign the policies into a manifest using the private key
    from the environment."""
    import os

    if "FILEGIT_PRIVATE_KEY" not in os.environ:
        raise HTTPException(
            status_code=400,
            detail=(
                "FILEGIT_PRIVATE_KEY environment variable is not set. "
                "Cannot sign the policies."
            ),
        )

    uc = get_use_cases()
    repo_path = Path.cwd()
    try:
        manifest = uc.pack(repo_path)
        return {"status": "success", "manifest": manifest.model_dump(mode="json")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def serve() -> None:
    repo_path = Path(__file__).parent.parent.parent.parent.parent
    dashboard_dist = repo_path / "dashboard" / "dist"

    # Mount static files if they exist (production mode)
    if dashboard_dist.exists():
        app.mount(
            "/", StaticFiles(directory=str(dashboard_dist), html=True), name="dashboard"
        )

    uvicorn.run(app, host="127.0.0.1", port=3000)
