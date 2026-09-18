"""
Device Repository module with Redis caching for connected ADB & Over-IP devices.
"""
from typing import List, Dict, Any, Optional

from repositories.base_repository import BaseRepository
import ui.db_manager as ui_db
import ui.stats_manager as ui_stats
import over_ip.db as over_ip_db
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

        # 1. Local Storage
        if device_id in ("local", "default", ""):
            from repositories import song_repo
            songs = song_repo.get_all_songs(force_refresh=force_refresh, progress_cb=progress_cb)
            return {
                "device_id": "local",
                "device_name": "Local Music Folders",
                "device_type": "Local Storage",
                "count": len(songs),
                "songs": songs
            }

        # 2. ADB Device
        if device_id.startswith("adb_") or device_id.startswith("adb:"):
            serial = device_id.split("_", 1)[-1] if "_" in device_id else device_id.split(":", 1)[-1]
            cache_key = f"cache:device_songs:adb_{serial}"
            if not force_refresh:
                cached = self._cache_get(cache_key)
                if cached is not None:
                    logger.info(f"[DeviceRepository] Cache Hit: Loaded ADB songs for {serial}.")
                    return cached

            import config_manager
            import adb_manager
            import song_parser

            cfg = config_manager.load_config()
            redis_cfg = self._get_redis_config()
            songs = []
            model = serial
            try:
                adb_devs = adb_manager.list_adb_devices()
                for d in adb_devs:
                    if d.get("serial") == serial:
                        model = d.get("model") or serial
                        break
            except Exception:
                pass

            if progress_cb:
                try:
                    progress_cb(f"[START] Querying music library from ADB device [{serial}] ({model})...")
                except Exception:
                    pass

            try:
                raw_out = adb_manager.query_songs_from_device(serial, redis_cfg=redis_cfg, refresh_cache=force_refresh)
                songs = song_parser.parse_songs(raw_out)
                logger.info(f"[DeviceRepository] Successfully queried {len(songs)} songs from ADB device [{serial}].")
                if progress_cb:
                    try:
                        progress_cb(f"[DONE] Found {len(songs)} song(s) on ADB device [{serial}].")
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"[DeviceRepository] Failed to query songs from ADB device {serial}: {e}")
                if progress_cb:
                    try:
                        progress_cb(f"[ERROR] Failed to query ADB device: {e}")
                    except Exception:
                        pass

            result = {
                "device_id": device_id,
                "device_name": f"Android ADB: {model}",
                "device_type": "ADB USB/Wi-Fi",
                "serial": serial,
                "count": len(songs),
                "songs": songs
            }
            self._cache_set(cache_key, result)
            return result

        # 3. Over-IP Peer
        if device_id.startswith("ip_") or device_id.startswith("ip:"):
            ip_addr = device_id.split("_", 1)[-1] if "_" in device_id else device_id.split(":", 1)[-1]
            cache_key = f"cache:device_songs:ip_{ip_addr}"
            if not force_refresh:
                cached = self._cache_get(cache_key)
                if cached is not None:
                    logger.info(f"[DeviceRepository] Redis Cache Hit: Loaded Over-IP songs for {ip_addr}.")
                    return cached

            import config_manager
            import over_ip.client as ip_client

            stored = self.get_stored_ip_hosts()
            port = 5000
            alias = ip_addr
            for h in stored:
                if h["ip_address"] == ip_addr:
                    port = h.get("port", 5000)
                    alias = h.get("alias") or ip_addr
                    break

            redis_cfg = self._get_redis_config()
            if progress_cb:
                try:
                    progress_cb(f"[START] Fetching songs from Over-IP host {ip_addr}:{port} ({alias})...")
                except Exception:
                    pass
            try:
                songs = ip_client.get_remote_songs(ip_addr, port=port, redis_cfg=redis_cfg, refresh=force_refresh)
                logger.info(f"[DeviceRepository] Successfully fetched {len(songs)} songs from Over-IP host {ip_addr}.")
                if progress_cb:
                    try:
                        progress_cb(f"[DONE] Found {len(songs)} song(s) on Over-IP host {ip_addr}.")
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"[DeviceRepository] Failed to fetch songs from Over-IP host {ip_addr}: {e}")
                if progress_cb:
                    try:
                        progress_cb(f"[ERROR] Failed to fetch songs from Over-IP host {ip_addr}: {e}")
                    except Exception:
                        pass
                songs = []

            result = {
                "device_id": device_id,
                "device_name": f"Over-IP Peer: {alias}",
                "device_type": "Over-IP HTTP",
                "ip": ip_addr,
                "port": port,
                "count": len(songs),
                "songs": songs
            }
            self._cache_set(cache_key, result)
            return result

        # Fallback to local
        from repositories import song_repo
        songs = song_repo.get_all_songs(force_refresh=force_refresh, progress_cb=progress_cb)
        return {
            "device_id": device_id,
            "device_name": device_id,
            "device_type": "Storage",
            "count": len(songs),
            "songs": songs
        }

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
        import os
        if not filepath:
            return {"status": "error", "message": "Missing filepath parameter", "code": 400}

        # 1. Local Storage
        if not device_id or device_id == "local":
            from repositories import song_repo
            return song_repo.delete_song(filepath)

        # 2. ADB Device
        if device_id.startswith("adb_") or device_id.startswith("adb:"):
            serial = device_id.split("_", 1)[-1] if "_" in device_id else device_id.split(":", 1)[-1]
            import adb_manager
            redis_cfg = self._get_redis_config()
            try:
                res = adb_manager.delete_song_from_device(
                    serial=serial,
                    filepath=filepath,
                    song_id=song_id,
                    redis_cfg=redis_cfg
                )
                # Invalidate device cache keys
                self._cache_delete(f"cache:device_songs:adb_{serial}")
                self._cache_delete(f"cache:device_songs:adb:{serial}")
                self._cache_delete("cache:devices:summary")
                self._cache_delete("cache:dashboard:stats")

                # Remove from synced_files history if present
                clean_filename = filename or os.path.basename(filepath)
                ui_db.remove_synced_file(serial, clean_filename)

                logger.info(f"[DeviceRepository] Successfully deleted song '{filepath}' from ADB device [{serial}].")
                return res
            except Exception as e:
                logger.error(f"[DeviceRepository] Failed to delete song from ADB device [{serial}]: {e}")
                return {"status": "error", "message": str(e), "code": 500}

        # 3. Over-IP Peer
        if device_id.startswith("ip_") or device_id.startswith("ip:"):
            ip_addr = device_id.split("_", 1)[-1] if "_" in device_id else device_id.split(":", 1)[-1]
            import over_ip.client as ip_client
            stored = self.get_stored_ip_hosts()
            port = 5000
            for h in stored:
                if h["ip_address"] == ip_addr:
                    port = h.get("port", 5000)
                    break
            try:
                res = ip_client.delete_remote_song(ip_addr, filepath, port=port)
                self._cache_delete(f"cache:device_songs:ip_{ip_addr}")
                self._cache_delete(f"cache:device_songs:ip:{ip_addr}")
                self._cache_delete("cache:devices:summary")
                self._cache_delete("cache:dashboard:stats")
                return res
            except Exception as e:
                logger.error(f"[DeviceRepository] Failed to delete song from Over-IP peer [{ip_addr}]: {e}")
                return {"status": "error", "message": str(e), "code": 500}

        return {"status": "error", "message": f"Unsupported device: {device_id}", "code": 400}

    def delete_device_songs_batch(
        self,
        device_id: str,
        filepaths: List[str]
    ) -> Dict[str, Any]:
        """
        Delete multiple audio files from a connected device in batch.
        """
        if not device_id or device_id == "local":
            from repositories import song_repo
            return song_repo.delete_songs_batch(filepaths)

        # For ADB or Over-IP devices, delete iteratively
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
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Push or upload a single local audio track to a target device (ADB or Over-IP peer).
        """
        import os
        if not local_filepath or not os.path.exists(local_filepath):
            return {"status": "error", "message": f"Local file not found: {local_filepath}", "code": 404}

        abs_path = os.path.abspath(local_filepath)
        filename = os.path.basename(abs_path)

        # 1. ADB Device
        if device_id.startswith("adb_") or device_id.startswith("adb:"):
            serial = device_id.split("_", 1)[-1] if "_" in device_id else device_id.split(":", 1)[-1]
            import adb_pusher
            import config_manager
            cfg = config_manager.load_config()
            target_dir = remote_dir or cfg.get("remote_adb_folder", "/storage/emulated/0/Music/ADB")
            redis_cfg = self._get_redis_config()

            try:
                success = adb_pusher.push_song_to_device(serial, abs_path, target_dir, redis_cfg=redis_cfg)
                if not success:
                    return {"status": "error", "message": f"Failed to push {filename} to ADB device [{serial}]", "code": 500}

                # Invalidate caches
                self._cache_delete(f"cache:device_songs:adb_{serial}")
                self._cache_delete(f"cache:device_songs:adb:{serial}")
                self._cache_delete("cache:devices:summary")
                self._cache_delete("cache:dashboard:stats")

                dest_path = f"{target_dir}/{filename}"
                logger.info(f"[DeviceRepository] Successfully pushed '{filename}' to ADB device [{serial}] -> {dest_path}")
                return {
                    "status": "success",
                    "message": f"Successfully synced '{filename}' to ADB device [{serial}].",
                    "dest_path": dest_path
                }
            except Exception as e:
                logger.error(f"[DeviceRepository] Error pushing song to ADB device [{serial}]: {e}")
                return {"status": "error", "message": str(e), "code": 500}

        # 2. Over-IP Peer
        if device_id.startswith("ip_") or device_id.startswith("ip:"):
            ip_addr = device_id.split("_", 1)[-1] if "_" in device_id else device_id.split(":", 1)[-1]
            import over_ip.client as ip_client
            stored = self.get_stored_ip_hosts()
            port = 5000
            for h in stored:
                if h["ip_address"] == ip_addr:
                    port = h.get("port", 5000)
                    break
            try:
                uploaded = ip_client.upload_song_to_peer(ip_addr, abs_path, port=port)
                if not uploaded:
                    return {"status": "error", "message": f"Failed to upload {filename} to Over-IP peer {ip_addr}:{port}", "code": 500}

                # Invalidate caches
                self._cache_delete(f"cache:device_songs:ip_{ip_addr}")
                self._cache_delete(f"cache:device_songs:ip:{ip_addr}")
                self._cache_delete("cache:devices:summary")
                self._cache_delete("cache:dashboard:stats")

                logger.info(f"[DeviceRepository] Successfully uploaded '{filename}' to Over-IP peer [{ip_addr}].")
                return {
                    "status": "success",
                    "message": f"Successfully synced '{filename}' to Over-IP peer [{ip_addr}:{port}].",
                    "dest_path": f"Remote host {ip_addr}"
                }
            except Exception as e:
                logger.error(f"[DeviceRepository] Error uploading song to Over-IP peer [{ip_addr}]: {e}")
                return {"status": "error", "message": str(e), "code": 500}

        return {"status": "error", "message": f"Unsupported sync target device: {device_id}", "code": 400}


