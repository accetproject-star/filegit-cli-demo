from filegit.infrastructure.hasher import SHA256Hasher
from filegit.domain.errors import FileGitError
import pytest
import hashlib

def test_hash_file(temp_repo):
    test_file = temp_repo / "test.txt"
    test_file.write_text("test content")
    
    hasher = SHA256Hasher()
    result = hasher.hash_file(test_file)
    
    expected = hashlib.sha256(b"test content").hexdigest()
    assert result == f"sha256:{expected}"

def test_hash_file_not_found(temp_repo):
    hasher = SHA256Hasher()
    with pytest.raises(FileGitError):
        hasher.hash_file(temp_repo / "nonexistent.txt")
