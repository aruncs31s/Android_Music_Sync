"""
Base abstractions and protocols for Device Providers.
Adheres to Interface Segregation Principle (ISP) and Liskov Substitution Principle (LSP).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Generator, Tuple


@dataclass
class PushResult:
    """Standardized result of a push/upload operation."""
    success: bool
    filepath: str
    message: str = ""
    dest_path: str = ""
    error: str = ""
    bytes_transferred: int = 0
    transcoded: bool = False
    original_bitrate: Optional[int] = None
    transcoded_bitrate: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": "success" if self.success else "error",
            "success": self.success,
            "filepath": self.filepath,
            "message": self.message,
            "dest_path": self.dest_path,
            "error": self.error,
            "bytes_transferred": self.bytes_transferred,
            "transcoded": self.transcoded,
            "original_bitrate": self.original_bitrate,
            "transcoded_bitrate": self.transcoded_bitrate,
        }


@dataclass
class DeleteResult:
    """Standardized result of a delete operation on a target device."""
    success: bool
    filepath_or_id: str
    message: str = ""
    code: int = 200

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": "success" if self.success else "error",
            "message": self.message,
            "code": self.code,
        }


class SongQueryable(ABC):
    """Interface for devices that can list/query their songs."""

    @abstractmethod
    def get_songs(
        self,
        force_refresh: bool = False,
        progress_cb: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """Query and return song list for this device."""
        pass


class SongPushable(ABC):
    """Interface for devices that can receive songs (push/upload)."""

    @abstractmethod
    def push_song(
        self,
        local_filepath: str,
        remote_dir: Optional[str] = None,
        filename: Optional[str] = None
    ) -> PushResult:
        """Push a local audio file to this device."""
        pass


class SongDeletable(ABC):
    """Interface for devices that support deleting tracks remotely."""

    @abstractmethod
    def delete_song(
        self,
        filepath_or_id: str,
        filename: Optional[str] = None
    ) -> DeleteResult:
        """Delete a song from this device."""
        pass


class SongStreamable(ABC):
    """Interface for devices that can stream audio files."""

    @abstractmethod
    def stream_song(
        self,
        filepath_or_id: str,
        range_header: Optional[str] = None
    ) -> Any:
        """Provide audio stream (generator or Response) for playback."""
        pass


class DeviceProvider(SongQueryable, SongPushable, SongDeletable, SongStreamable, ABC):
    """
    Unified abstract base class for a music device.
    Subclasses (LocalDeviceProvider, AdbDeviceProvider, OverIpDeviceProvider)
    can be substituted anywhere a DeviceProvider is expected (LSP).
    """

    def __init__(self, device_id: str):
        self.device_id = device_id

    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """Return metadata about the device (id, name, type, online status)."""
        pass
