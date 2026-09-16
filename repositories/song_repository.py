"""
Song Repository module with Redis caching and disk fallback.
"""
import os
import sys
import socket
from typing import List, Dict, Any, Optional

from repositories.base_repository import BaseRepository
import config_manager
import over_ip.song_scanner as song_scanner
import ui.stats_manager as ui_stats
import audio_metadata
import ui.db_manager as ui_db
import hide_list_db
from utils import get_logger

logger = get_logger()


class SongRepository(BaseRepository):
    """
    Repository for managing local music library scanning, duplicate detection,
    and song file deletion with Redis caching awareness.
    """

    CACHE_KEY_ALL_SONGS = "cache:songs:all"
    CACHE_KEY_DUPLICATES = "cache:songs:duplicates"

    def get_all_songs(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch all local music library songs sorted by mtime descending.
        Checks Redis cache first if enabled; scans disk folders on cache miss.
        """
        if not force_refresh:
            cached = self._cache_get(self.CACHE_KEY_ALL_SONGS)
            if cached is not None:
                logger.info("[SongRepository] Redis Cache Hit: Loaded songs library.")
                return cached

        logger.info("[SongRepository] Cache miss / scan requested: Scanning disk directories...")
        cfg = config_manager.load_config()
        folders = config_manager.get_local_sync_folders(cfg)
        audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])
        songs = song_scanner.scan_songs_from_paths(folders, audio_exts)

        self._cache_set(self.CACHE_KEY_ALL_SONGS, songs)
        return songs

    def get_duplicates(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Detect duplicate song clusters across configured music directories.
        Checks Redis cache first if enabled; runs detection algorithm on cache miss.
        """
        if not force_refresh:
            cached = self._cache_get(self.CACHE_KEY_DUPLICATES)
            if cached is not None:
                logger.info("[SongRepository] Redis Cache Hit: Loaded duplicate clusters.")
                return cached

        songs = self.get_all_songs(force_refresh=force_refresh)
        dups = ui_stats.detect_duplicate_songs(songs)

        self._cache_set(self.CACHE_KEY_DUPLICATES, dups)
        return dups

    def delete_song(self, filepath: str) -> Dict[str, Any]:
        """
        Permanently delete an audio file from disk, invalidate in-memory metadata cache,
        remove database hide list references, and clear Redis song caches.
        """
        abs_path = os.path.abspath(filepath)
        if not os.path.exists(abs_path):
            return {"status": "error", "message": f"File does not exist: {abs_path}", "code": 404}

        try:
            os.remove(abs_path)
            # Remove from hide lists if present
            ui_db.remove_hidden_file(abs_path)
            hide_list_db.remove_hidden_file(abs_path)

            # Invalidate in-memory metadata cache
            audio_metadata.METADATA_CACHE.pop(abs_path, None)

            # Invalidate Redis song caches
            self.invalidate_all_song_caches()

            logger.info(f"[SongRepository] Successfully deleted audio file: {abs_path}")
            return {
                "status": "success",
                "message": f"Successfully deleted {os.path.basename(abs_path)}"
            }
        except Exception as e:
            logger.error(f"[SongRepository] Error deleting song '{abs_path}': {e}")
            return {"status": "error", "message": f"Failed to delete file: {e}", "code": 500}

    def invalidate_all_song_caches(self):
        """Clear all cached song data in Redis."""
        self._cache_delete(self.CACHE_KEY_ALL_SONGS)
        self._cache_delete(self.CACHE_KEY_DUPLICATES)
        # Clear legacy redis hostname key if present
        try:
            hostname_key = f"over_ip_songs:{socket.gethostname()}"
            self._cache_delete(hostname_key)
        except Exception:
            pass
