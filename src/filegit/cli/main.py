import typer
from typing import Optional
from pathlib import Path
from rich.console import Console

from filegit.core.use_cases import FileGitUseCases
from filegit.infrastructure.crypto import PyNaClCrypto
from filegit.infrastructure.hasher import SHA256Hasher
from filegit.infrastructure.fs import OSFileSystem
from filegit.domain.errors import FileGitError

app = typer.Typer(help="FileGit CLI: Agentic governance and context attestation.")
console = Console()

def get_use_cases() -> FileGitUseCases:
    return FileGitUseCases(
        crypto=PyNaClCrypto(),
        hasher=SHA256Hasher(),
        fs=OSFileSystem()
    )

@app.command()
def init(
    repo_path: Path = typer.Option(Path.cwd(), help="Path to the repository to initialize.")
):
    """Initialize a FileGit context repository."""
    try:
        uc = get_use_cases()
        uc.init_repo(repo_path)
        console.print(f"[green]✔[/green] FileGit repository initialized at [bold]{repo_path / '.filegit'}[/bold]")
    except FileGitError as e:  # pragma: no cover
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

@app.command()
def keygen(
    key_dir: Path = typer.Option(Path.home() / ".filegit" / "keys", help="Directory to store keys.")
):
    """Generate Ed25519 keypair for manifest signing."""
    try:
        uc = get_use_cases()
        priv, pub = uc.generate_keys(key_dir)
        console.print(f"[green]✔[/green] Keys generated successfully.")
        console.print(f"  [bold]Private Key:[/bold] {priv} (Keep this secure!)")
        console.print(f"  [bold]Public Key:[/bold]  {pub}")
    except FileGitError as e:  # pragma: no cover
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

@app.command()
def pack(
    repo_path: Path = typer.Option(Path.cwd(), help="Path to the repository."),
    key_path: Optional[Path] = typer.Option(None, help="Path to the private key file. Overrides FILEGIT_PRIVATE_KEY env var.")
):
    """Pack and sign a new context bundle manifest."""
    try:
        uc = get_use_cases()
        manifest = uc.pack(repo_path, key_path)
        console.print(f"[green]✔[/green] Bundle packed successfully.")
        console.print(f"  [bold]Bundle ID:[/bold] {manifest.id}")
        console.print(f"  [bold]Manifest:[/bold]   {repo_path / '.filegit' / 'manifest.json'}")
    except FileGitError as e:  # pragma: no cover
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

@app.command()
def verify(
    repo_path: Path = typer.Option(Path.cwd(), help="Path to the repository."),
    manifest_path: Optional[Path] = typer.Option(None, help="Path to the manifest.json.")
):
    """Verify the integrity and signature of the context bundle."""
    if not manifest_path:
        manifest_path = repo_path / ".filegit" / "manifest.json"
        
    try:
        uc = get_use_cases()
        is_valid = uc.verify(repo_path, manifest_path)
        if is_valid:
            console.print("[green]✔[/green] [bold]VERIFIED:[/bold] The context bundle is authentic and unmodified.")
    except FileGitError as e:  # pragma: no cover
        console.print(f"[red]❌ BLOCK:[/red] Verification failed.")
        console.print(f"  [red]Reason:[/red] {e}")
        raise typer.Exit(code=1)

@app.command()
def mcp():  # pragma: no cover
    """Run the FileGit MCP Server for AI Agents."""
    try:
        import asyncio
        from filegit.cli.mcp_server import serve
        asyncio.run(serve())
    except ImportError as e:
        console.print("[red]Error:[/red] The 'mcp' dependency is not installed. Please install it using 'pip install mcp'.")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":  # pragma: no cover
    app()
