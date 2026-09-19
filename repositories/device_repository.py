"""
Device Repository module with Redis caching for connected ADB & Over-IP devices.
"""
import os
from typing import List, Dict, Any, Optional

from repositories.base_repository import BaseRepository
import ui.db_manager as ui_db
import ui.stats_manager as ui_stats
import over_ip.db as over_ip_db
from device_providers.registry import DeviceProviderRegistry
from services.audio_transcoder import AudioTranscoder
from utils import get_logger

logger = get_logger()


class DeviceRepository(BaseRepository):
    """
    Repository for managing Over-IP peer hosts and ADB connected devices
    with Redis cache-awareness.
    """

    CACHE_KEY_IP_HOSTS = "cache:devices:ip_hosts"

    def get_stored_ip_hosts(self) -> List[Dict[str, Any]]:
        """
        Fetch stored Over-IP hosts.
        Checks Redis cache first; queries SQLite on cache miss.
        """
        cached = self._cache_get(self.CACHE_KEY_IP_HOSTS)
        if cached is not None:
            logger.info("[DeviceRepository] Redis Cache Hit: Loaded IP hosts.")
            return cached

        hosts = ui_db.get_stored_ip_hosts()
        self._cache_set(self.CACHE_KEY_IP_HOSTS, hosts)
        return hosts

    def add_ip_host(self, ip_address: str, port: int = 5000, alias: str = "") -> bool:
        """
        Add or update an IP host entry in database/db.db and invalidate Redis cache.
        """
        success = over_ip_db.add_ip_host(ip_address, port, alias)
        if success:
            self._cache_delete(self.CACHE_KEY_IP_HOSTS)
        return success

    def update_ip_status(self, ip_address: str, is_online: bool) -> bool:
        """
        Update online status for an IP host and invalidate Redis cache.
        """
        success = over_ip_db.update_ip_status(ip_address, is_online)
        if success:
            self._cache_delete(self.CACHE_KEY_IP_HOSTS)
        return success

    def get_synced_records(self, device_serial: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch synced track records by device serial.
        """
        return ui_db.get_all_synced_records(device_serial)

    def get_device_songs(self, device_id: str, force_refresh: bool = False, progress_cb=None) -> Dict[str, Any]:
        """
        Fetch all songs for a specified device (Local, ADB, Over-IP) with Redis caching.
        Returns a dictionary containing device metadata and the list of song dicts.
        """
        device_id = (device_id or "local").strip()
        cache_key = f"cache:device_songs:{device_id.replace(':', '_')}"

        if not force_refresh:
            cached = self._cache_get(cache_key)
            if cached is not None:
                logger.info(f"[DeviceRepository] Cache Hit: Loaded songs for {device_id}.")
                return cached

        provider = DeviceProviderRegistry.get_provider(device_id)
        info = provider.get_device_info()
        songs = provider.get_songs(force_refresh=force_refresh, progress_cb=progress_cb)

        result = {
            "device_id": device_id,
            "device_name": info.get("device_name", device_id),
            "device_type": info.get("device_type", "Connected Device"),
            "count": len(songs),
            "songs": songs
        }
        if "serial" in info:
            result["serial"] = info["serial"]
        if "ip" in info:
            result["ip"] = info["ip"]
            result["port"] = info.get("port", 5000)

        self._cache_set(cache_key, result)
        return result

    def delete_device_song(
        self,
        device_id: str,
        filepath: str,
        song_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a song from a connected device (Local, ADB, or Over-IP peer)
        and invalidate relevant caches.
        """
        if not filepath:
            return {"status": "error", "message": "Missing filepath parameter", "code": 400}

        device_id = (device_id or "local").strip()
        provider = DeviceProviderRegistry.get_provider(device_id)
        del_res = provider.delete_song(filepath_or_id=filepath, filename=filename)

        # Invalidate caches
        self._cache_delete(f"cache:device_songs:{device_id.replace(':', '_')}")
        self._cache_delete("cache:devices:summary")
        self._cache_delete("cache:dashboard:stats")

        return del_res.to_dict()

    def delete_device_songs_batch(
        self,
        device_id: str,
        filepaths: List[str]
    ) -> Dict[str, Any]:
        """
        Delete multiple audio files from a connected device in batch.
        """
        device_id = (device_id or "local").strip()
        if not device_id or device_id == "local":
            from repositories import song_repo
            return song_repo.delete_songs_batch(filepaths)

        deleted_count = 0
        failed = []
        for fp in filepaths:
            res = self.delete_device_song(device_id=device_id, filepath=fp)
            if res.get("status") == "success":
                deleted_count += 1
            else:
                failed.append({"filepath": fp, "error": res.get("message", "Failed to delete")})

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "failed": failed,
            "message": f"Deleted {deleted_count} files from {device_id}"
        }

    def push_song_to_device(
        self,
        device_id: str,
        local_filepath: str,
        remote_dir: Optional[str] = None,
        force: bool = False,
        target_bitrate: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Push or upload a single local audio track to a target device (ADB or Over-IP peer).
        Supports on-the-fly audio downconversion if target_bitrate is provided.
        """
        if not local_filepath or not os.path.exists(local_filepath):
            return {"status": "error", "message": f"Local file not found: {local_filepath}", "code": 404}

        abs_path = os.path.abspath(local_filepath)
        filename = os.path.basename(abs_path)
        device_id = (device_id or "local").strip()
        provider = DeviceProviderRegistry.get_provider(device_id)

        try:
            with AudioTranscoder.managed_transcode(abs_path, target_bitrate_kbps=target_bitrate) as (file_to_send, was_transcoded):
                push_res = provider.push_song(file_to_send, remote_dir=remote_dir, filename=filename)

            if push_res.success:
                # Invalidate caches
                self._cache_delete(f"cache:device_songs:{device_id.replace(':', '_')}")
                self._cache_delete("cache:devices:summary")
                self._cache_delete("cache:dashboard:stats")

                if hasattr(provider, "serial"):
                    ui_db.add_synced_file(abs_path, filename, provider.serial, remote_dir or "")

                return {
                    "status": "success",
                    "message": push_res.message or f"Successfully synced '{filename}'.",
                    "dest_path": push_res.dest_path,
                    "transcoded": was_transcoded,
                    "target_bitrate": target_bitrate if was_transcoded else None
                }
            else:
                return {
                    "status": "error",
                    "message": push_res.error or f"Failed to push {filename} to {device_id}",
                    "code": 500
                }
        except Exception as e:
            logger.error(f"[DeviceRepository] Error pushing {filename} to {device_id}: {e}")
            return {"status": "error", "message": str(e), "code": 500}


