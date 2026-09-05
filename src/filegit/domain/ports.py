import abc
from pathlib import Path
from typing import Dict, Optional

class CryptoPort(abc.ABC):
    @abc.abstractmethod
    def generate_keypair(self) -> tuple[bytes, bytes]:
        """Generates an Ed25519 keypair. Returns (private_key_bytes, public_key_bytes)."""
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_public_key(self, private_key: bytes) -> bytes:
        """Derives public key from private key."""
        pass  # pragma: no cover
        
    @abc.abstractmethod
    def sign(self, private_key: bytes, message: bytes) -> str:
        """Signs a message using the private key. Returns base58 encoded signature."""
        pass  # pragma: no cover
        
    @abc.abstractmethod
    def verify(self, public_key: bytes, message: bytes, signature: str) -> bool:
        """Verifies a base58 signature against a message and public key."""
        pass  # pragma: no cover

class HashingPort(abc.ABC):
    @abc.abstractmethod
    def hash_file(self, path: Path) -> str:
        """Computes SHA-256 hash of a file. Returns 'sha256:<hex>'."""
        pass  # pragma: no cover

class FileSystemPort(abc.ABC):
    @abc.abstractmethod
    def ensure_dir(self, path: Path) -> None:
        """Ensures a directory exists."""
        pass  # pragma: no cover
        
    @abc.abstractmethod
    def read_text(self, path: Path) -> str:
        """Reads text from a file."""
        pass  # pragma: no cover
        
    @abc.abstractmethod
    def write_text(self, path: Path, content: str) -> None:
        """Writes text to a file."""
        pass  # pragma: no cover
        
    @abc.abstractmethod
    def iter_markdown_files(self, directory: Path) -> list[Path]:
        """Iterates over all .md files in a directory."""
        pass  # pragma: no cover
