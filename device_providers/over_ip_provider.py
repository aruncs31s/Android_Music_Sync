"""
Over-IP Device Provider for wireless communication with Android companion apps.
Implements query, upload/push, delete, and audio streaming proxying (SRP / ISP).
"""
import os
import requests
from typing import List, Dict, Any, Optional, Callable, Tuple
import over_ip.client as ip_client
import database.db_manager as ui_db
import config_manager
from device_providers.base import DeviceProvider, PushResult, DeleteResult
from utils import get_logger

logger = get_logger()


class OverIpDeviceProvider(DeviceProvider):
    """Manages audio operations for remote Android devices communicating over HTTP."""

    def __init__(self, device_id: str):
        super().__init__(device_id=device_id)
        if device_id.startswith("ip_"):
            self.ip = device_id.split("_", 1)[-1]
        elif device_id.startswith("ip:"):
            self.ip = device_id.split(":", 1)[-1]
        elif "://" in device_id:
            from urllib.parse import urlparse
            parsed = urlparse(device_id)
            self.ip = parsed.hostname or device_id
            if parsed.port:
                self.port = parsed.port
        else:
            self.ip = device_id

        # Resolve port and alias from database
        self.port = 5000
        self.alias = self.ip
        try:
            stored = ui_db.get_stored_ip_hosts()
            for h in stored:
                if h.get("ip_address") == self.ip:
                    self.port = h.get("port", 5000)
                    self.alias = h.get("alias") or self.ip
                    break
        except Exception:
            pass

    def get_device_info(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "ip": self.ip,
            "port": self.port,
            "device_name": f"Over-IP Peer: {self.alias}",
            "device_type": "Over-IP HTTP",
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
                progress_cb(f"[START] Fetching songs from Over-IP host {self.ip}:{self.port} ({self.alias})...")
            except Exception:
                pass

        try:
            songs = ip_client.get_remote_songs(self.ip, port=self.port, redis_cfg=redis_cfg, refresh=force_refresh)
            logger.info(f"[OverIpDeviceProvider] Acquired {len(songs)} songs from {self.ip}:{self.port}.")
            if progress_cb:
                try:
                    progress_cb(f"[DONE] Found {len(songs)} song(s) on Over-IP host {self.ip}.")
                except Exception:
                    pass
            return songs
        except Exception as e:
            logger.error(f"[OverIpDeviceProvider] Failed to fetch songs from {self.ip}: {e}")
            if progress_cb:
                try:
                    progress_cb(f"[ERROR] Failed to fetch songs from Over-IP host: {e}")
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
        clean_name = filename or os.path.basename(abs_path)

        try:
            uploaded = ip_client.upload_song_to_peer(self.ip, abs_path, port=self.port)
            if uploaded:
                return PushResult(
                    success=True,
                    filepath=abs_path,
                    dest_path=f"Remote {self.ip}:{self.port}",
                    message=f"Successfully uploaded '{clean_name}' to Over-IP peer [{self.alias}].",
                    bytes_transferred=os.path.getsize(abs_path)
                )
            return PushResult(
                success=False,
                filepath=abs_path,
                error=f"HTTP upload to {self.ip}:{self.port} returned unsuccessful status."
            )
        except Exception as e:
            logger.error(f"[OverIpDeviceProvider] Upload error to {self.ip}: {e}")
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
        try:
            res = ip_client.delete_remote_song(self.ip, filepath_or_id, port=self.port)
            if res.get("status") == "success":
                return DeleteResult(
                    success=True,
                    filepath_or_id=filepath_or_id,
                    message=f"Deleted '{filename or filepath_or_id}' from Over-IP peer."
                )
            return DeleteResult(
                success=False,
                filepath_or_id=filepath_or_id,
                message=res.get("message", "Delete failed"),
                code=res.get("code", 500)
            )
        except Exception as e:
            logger.error(f"[OverIpDeviceProvider] Delete error on {self.ip}: {e}")
            return DeleteResult(success=False, filepath_or_id=filepath_or_id, message=str(e), code=500)

    def stream_song(
        self,
        filepath_or_id: str,
        range_header: Optional[str] = None
    ) -> Tuple[Any, int, Dict[str, str]]:
        """
        Connect to remote Over-IP companion app at /api/song/stream and stream chunks.
        Returns (response_stream, status_code, response_headers).
        """
        base_url = ip_client.get_base_url(self.ip, self.port)
        url = f"{base_url}/api/song/stream"
        params = {"filepath": filepath_or_id}
        headers = {}
        if range_header:
            headers["Range"] = range_header

        req = requests.get(url, params=params, headers=headers, stream=True, timeout=10.0)
        status_code = req.status_code

        res_headers = {}
        for h in ("Content-Type", "Content-Length", "Content-Range", "Accept-Ranges"):
            if h in req.headers:
                res_headers[h] = req.headers[h]

        return req, status_code, res_headers
