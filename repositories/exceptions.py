from typing import Any, Dict, Optional


class MusicSyncError(Exception):
    """
    Base domain exception for all Antigravity Music Sync operations.
    Includes HTTP status code and optional structured details for clean API responses.
    """

    def __init__(
        self,
        message: str,
        code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {"error": self.message, "code": self.code}
        if self.details:
            res["details"] = self.details
        return res


class ResourceNotFoundError(MusicSyncError):
    """Raised when a requested resource (song, playlist, device) cannot be found."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=404, details=details)


class PlaylistNotFoundError(ResourceNotFoundError):
    """Raised when a playlist ID or name does not exist."""
    pass


class TrackNotFoundError(ResourceNotFoundError):
    """Raised when a track filepath or record does not exist."""
    pass


class DeviceNotFoundError(ResourceNotFoundError):
    """Raised when a target device is not connected or registered."""
    pass


class ValidationError(MusicSyncError):
    """Raised when input parameters or payload fail validation."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)


class DatabaseOperationError(MusicSyncError):
    """Raised when a database query, transaction, or mutation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=500, details=details)


class TrashFileMissingError(ResourceNotFoundError):
    """Raised when the temporary trash file does not exist."""

    def __init__(self, message: str):
        super().__init__(message)
        self.code = 404


class FileMoveError(MusicSyncError):
    """Raised when moving the file from trash to destination fails."""

    def __init__(self, message: str):
        super().__init__(message, code=500)
