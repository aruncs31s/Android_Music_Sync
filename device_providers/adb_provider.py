"""
ADB Device Provider for interacting with Android devices connected via USB or Wi-Fi.
Encapsulates ADB operations (query, push, delete) adhering to Single Responsibility Principle (SRP).
"""
import os
from typing import List, Dict, Any, Optional, Callable
import utils.android.adb.adb_manager as adb_manager
import utils.android.adb.adb_pusher as adb_pusher
import utils.config_manager as config_manager
import utils.android.adb.song_parser as song_parser
from device_providers.base import DeviceProvider, PushResult, DeleteResult
from utils import get_logger

logger = get_logger()


class AdbDeviceProvider(DeviceProvider):
    """Manages audio operations for Android devices connected via ADB."""

    def __init__(self, device_id: str):
        super().__init__(device_id=device_id)
        if device_id.startswith("adb_"):
            self.serial = device_id.split("_", 1)[-1]
        elif device_id.startswith("adb:"):
            self.serial = device_id.split(":", 1)[-1]
        else:
            self.serial = device_id

    def get_device_info(self) -> Dict[str, Any]:
        model = self.serial
        try:
            devs = adb_manager.list_adb_devices()
            for d in devs:
                if d.get("serial") == self.serial:
                    model = d.get("model") or self.serial
                    break
        except Exception:
            pass

        return {
            "device_id": self.device_id,
            "serial": self.serial,
            "device_name": f"Android ADB: {model}",
            "device_type": "ADB USB/Wi-Fi",
            "is_online": True,
        }

    def get_songs(
        self,
        force_refresh: bool = False,
        progress_cb: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        cfg = config_manager.load_config()
        redis_cfg = cfg.get("redis")
        if progress_cb:
            try:
                progress_cb(f"[START] Querying music library from ADB device [{self.serial}]...")
            except Exception:
                pass

        try:
            raw_out = adb_manager.query_songs_from_device(self.serial, redis_cfg=redis_cfg, refresh_cache=force_refresh)
            songs = song_parser.parse_songs(raw_out)
            if progress_cb:
                try:
                    progress_cb(f"[DONE] Found {len(songs)} song(s) on ADB device [{self.serial}].")
                except Exception:
                    pass
            return songs
        except Exception as e:
            logger.error(f"[AdbDeviceProvider] Failed to query songs from ADB [{self.serial}]: {e}")
            if progress_cb:
                try:
                    progress_cb(f"[ERROR] Failed to query ADB device: {e}")
                except Exception:
                    pass
            return []

    def push_song(
        self,
        local_filepath: str,
        remote_dir: Optional[str] = None,
        filename: Optional[str] = None
    ) -> PushResult:
        if not os.path.exists(local_filepath):
            return PushResult(
                success=False,
                filepath=local_filepath,
                error=f"Local file not found: {local_filepath}"
            )

        abs_path = os.path.abspath(local_filepath)
        clean_filename = filename or os.path.basename(abs_path)
        cfg = config_manager.load_config()
        target_dir = remote_dir or cfg.get("remote_adb_folder", "/storage/emulated/0/Music/ADB")
        redis_cfg = cfg.get("redis")

        try:
            ok = adb_pusher.push_song_to_device(self.serial, abs_path, target_dir, redis_cfg=redis_cfg)
            dest_path = f"{target_dir}/{clean_filename}"
            if ok:
                return PushResult(
                    success=True,
                    filepath=abs_path,
                    dest_path=dest_path,
                    message=f"Successfully pushed '{clean_filename}' to ADB device [{self.serial}]."
                )
            return PushResult(
                success=False,
                filepath=abs_path,
                dest_path=dest_path,
                error=f"ADB push command failed for {clean_filename}"
            )
        except Exception as e:
            logger.error(f"[AdbDeviceProvider] Error pushing {abs_path} to ADB [{self.serial}]: {e}")
            return PushResult(
                success=False,
                filepath=abs_path,
                error=str(e)
            )

    def delete_song(
        self,
        filepath_or_id: str,
        filename: Optional[str] = None
    ) -> DeleteResult:
        clean_filename = filename or os.path.basename(filepath_or_id)
        try:
            res = adb_manager.delete_song_from_device(
                self.serial,
                filepath=filepath_or_id,
                filename=clean_filename
            )
            if res.get("status") == "success":
                import database.db_manager as ui_db
                ui_db.remove_synced_file(self.serial, clean_filename)
                return DeleteResult(success=True, filepath_or_id=filepath_or_id, message="Successfully deleted track from ADB device.")
            return DeleteResult(
                success=False,
                filepath_or_id=filepath_or_id,
                message=res.get("message", "ADB delete failed"),
                code=res.get("code", 500)
            )
        except Exception as e:
            logger.error(f"[AdbDeviceProvider] Failed to delete track from ADB [{self.serial}]: {e}")
            return DeleteResult(success=False, filepath_or_id=filepath_or_id, message=str(e), code=500)

    def stream_song(
        self,
        filepath_or_id: str,
        range_header: Optional[str] = None
    ) -> Any:
        raise NotImplementedError("Streaming directly from ADB device is not currently supported.")
