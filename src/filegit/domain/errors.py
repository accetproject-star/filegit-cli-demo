class FileGitError(Exception):
    """Base exception for all FileGit errors."""
    pass

class ManifestError(FileGitError):
    """Raised when there is an issue reading or validating the manifest."""
    pass

class SignatureError(FileGitError):
    """Raised when cryptographic signatures fail validation."""
    pass

class HashMismatchError(FileGitError):
    """Raised when the computed hash does not match the manifest hash."""
    pass

class KeyError(FileGitError):
    """Raised when there is an issue with loading or using cryptographic keys."""
    pass

class ConfigError(FileGitError):
    """Raised when there is a configuration issue."""
    pass
