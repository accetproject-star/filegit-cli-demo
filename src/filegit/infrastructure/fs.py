from pathlib import Path
from filegit.domain.ports import FileSystemPort
from filegit.domain.errors import FileGitError

class OSFileSystem(FileSystemPort):
    def ensure_dir(self, path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as e:  # pragma: no cover
            raise FileGitError(f"Failed to create directory {path}: {e}")

    def read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:  # pragma: no cover
            raise FileGitError(f"Failed to read file {path}: {e}")

    def write_text(self, path: Path, content: str) -> None:
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as e:  # pragma: no cover
            raise FileGitError(f"Failed to write file {path}: {e}")

    def iter_markdown_files(self, directory: Path) -> list[Path]:
        if not directory.exists() or not directory.is_dir():
            return []
        return list(directory.rglob("*.md"))
