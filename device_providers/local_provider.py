"""
Local Device Provider for accessing songs stored on the host computer.
Implements DeviceProvider adhering to Single Responsibility Principle (SRP).
"""
import os
from typing import List, Dict, Any, Optional, Callable
from device_providers.base import DeviceProvider, PushResult, DeleteResult
from utils import get_logger

logger = get_logger()


class LocalDeviceProvider(DeviceProvider):
    """Manages audio operations for host machine local library directories."""

    def __init__(self, device_id: str = "local"):
        super().__init__(device_id="local")

    def get_device_info(self) -> Dict[str, Any]:
        return {
            "device_id": "local",
            "device_name": "Local Storage",
            "device_type": "Local Storage",
            "is_online": True,
        }

    def get_songs(
        self,
        force_refresh: bool = False,
        progress_cb: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        from repositories import song_repo
        return song_repo.get_all_songs(force_refresh=force_refresh, progress_cb=progress_cb)

    def push_song(
        self,
        local_filepath: str,
        remote_dir: Optional[str] = None,
        filename: Optional[str] = None
    ) -> PushResult:
        """For local storage, a push is a copy or verification of presence."""
        if not os.path.exists(local_filepath):
            return PushResult(
                success=False,
                filepath=local_filepath,
                error=f"Local file does not exist: {local_filepath}",
            )
        return PushResult(
            success=True,
            filepath=local_filepath,
            dest_path=os.path.abspath(local_filepath),
            message="File already present in local library.",
        )

    def delete_song(
        self,
        filepath_or_id: str,
        filename: Optional[str] = None
    ) -> DeleteResult:
        from repositories import song_repo
        res = song_repo.delete_song(filepath_or_id)
        if res.get("status") == "success":
            return DeleteResult(success=True, filepath_or_id=filepath_or_id, message="Moved to trash", code=200)
        return DeleteResult(
            success=False,
            filepath_or_id=filepath_or_id,
            message=res.get("message", "Delete failed"),
            code=res.get("code", 500)
        )

    def stream_song(
        self,
        filepath_or_id: str,
        range_header: Optional[str] = None
    ) -> Any:
        return filepath_or_id
