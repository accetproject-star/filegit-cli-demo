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
    repo_path: Path = typer.Option(Path("."), help="Path to the repository to verify"),
    require_trace: bool = typer.Option(False, help="Require a valid agent execution trace")
):
    """Verify the integrity of the FileGit authorized context."""
    from filegit.core.use_cases import FileGitUseCases
    from filegit.infrastructure.crypto import PyNaClCrypto
    from filegit.infrastructure.hasher import SHA256Hasher
    from filegit.infrastructure.fs import OSFileSystem
    from filegit.domain.errors import FileGitError, ManifestError, SignatureError, HashMismatchError
    
    uc = FileGitUseCases(PyNaClCrypto(), SHA256Hasher(), OSFileSystem())
    manifest_path = repo_path / ".filegit" / "manifest.json"
    
    try:
        is_valid = uc.verify(repo_path, manifest_path, require_trace=require_trace)
        if is_valid:
            console.print("[green]✔[/green] [bold]VERIFIED:[/bold] The context bundle is authentic and unmodified.")
    except (FileGitError, ManifestError, SignatureError, HashMismatchError) as e:  # pragma: no cover
        console.print(f"[red]❌ BLOCK:[/red] Verification failed.")
        console.print(f"  [red]Reason:[/red] {e}")
        raise typer.Exit(code=1)

@app.command()
def studio():
    """Start the FileGit Studio Dashboard (Web UI)."""
    try:
        from filegit.cli.studio_server import serve
        console.print("[green]Starting FileGit Studio on http://127.0.0.1:3000[/green]")
        serve()
    except ImportError as e:
        console.print("[red]Error:[/red] The 'fastapi' and 'uvicorn' dependencies are not installed.")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        pass

trace_app = typer.Typer(help="Manage execution traces for AI agents.")
app.add_typer(trace_app, name="trace")

@trace_app.command("record")
def trace_record(
    prompt: str = typer.Option(..., help="The prompt the agent is responding to"),
    action: str = typer.Option(..., help="The type of action performed"),
    description: str = typer.Option(..., help="Description of the action"),
    repo_path: Path = typer.Option(Path("."), help="Path to the repository")
):
    """Record a step in the execution trace."""
    from filegit.core.flight_recorder import FlightRecorder
    from filegit.core.use_cases import FileGitUseCases
    from filegit.infrastructure.crypto import PyNaClCrypto
    from filegit.infrastructure.hasher import SHA256Hasher
    from filegit.infrastructure.fs import OSFileSystem
    
    uc = FileGitUseCases(PyNaClCrypto(), SHA256Hasher(), OSFileSystem())
    recorder = FlightRecorder(uc)
    try:
        recorder.record_action(repo_path, prompt, action, description)
        console.print("[green]✔ Action recorded.[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

@trace_app.command("seal")
def trace_seal(
    agent_id: str = typer.Option("unknown-agent", help="Identifier of the AI agent"),
    bundle_id: str = typer.Option(..., help="The ID of the FileGit bundle this trace complies with"),
    repo_path: Path = typer.Option(Path("."), help="Path to the repository")
):
    """Seal the current trace and sign it."""
    from filegit.core.flight_recorder import FlightRecorder
    from filegit.core.use_cases import FileGitUseCases
    from filegit.infrastructure.crypto import PyNaClCrypto
    from filegit.infrastructure.hasher import SHA256Hasher
    from filegit.infrastructure.fs import OSFileSystem
    
    uc = FileGitUseCases(PyNaClCrypto(), SHA256Hasher(), OSFileSystem())
    recorder = FlightRecorder(uc)
    try:
        trace = recorder.seal_trace(repo_path, agent_id, bundle_id)
        console.print(f"[green]✔ Trace sealed and signed: {trace.trace_id}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
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
