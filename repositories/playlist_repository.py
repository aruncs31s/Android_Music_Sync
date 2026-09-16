"""
Playlist Repository module with Redis caching and SQLite database fallback.
"""
import os
from typing import List, Dict, Any, Optional

from repositories.base_repository import BaseRepository
import ui.db_manager as ui_db
import config_manager
import over_ip.song_scanner as song_scanner
from utils import get_logger

logger = get_logger()


class PlaylistRepository(BaseRepository):
    """
    Repository for managing playlists and playlist tracks in SQLite (database/db.db)
    with Redis cache-awareness.
    """

    CACHE_KEY_PLAYLISTS = "cache:playlists:all"
    CACHE_KEY_PLAYLIST_TRACKS_PREFIX = "cache:playlists:tracks:"

    def get_playlists(self) -> List[Dict[str, Any]]:
        """
        Fetch all playlists with track counts.
        Checks Redis cache first; queries SQLite on cache miss.
        """
        cached = self._cache_get(self.CACHE_KEY_PLAYLISTS)
        if cached is not None:
            logger.info("[PlaylistRepository] Redis Cache Hit: Loaded playlists.")
            return cached

        logger.info("[PlaylistRepository] Cache miss: Querying SQLite database for playlists...")
        playlists = ui_db.get_playlists()
        self._cache_set(self.CACHE_KEY_PLAYLISTS, playlists)
        return playlists

    def create_playlist(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Create a new playlist in SQLite database and invalidate playlists Redis cache.
        """
        result = ui_db.create_playlist(name)
        if result:
            self._cache_delete(self.CACHE_KEY_PLAYLISTS)
        return result

    def delete_playlist(self, playlist_id: int) -> bool:
        """
        Delete a playlist from SQLite database and invalidate Redis caches.
        """
        success = ui_db.delete_playlist(playlist_id)
        if success:
            self._cache_delete(self.CACHE_KEY_PLAYLISTS)
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_TRACKS_PREFIX}{playlist_id}")
        return success

    def get_playlist_tracks(self, playlist_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve tracks for a playlist with metadata enrichment.
        Checks Redis cache first; queries SQLite and scans metadata on cache miss.
        """
        cache_key = f"{self.CACHE_KEY_PLAYLIST_TRACKS_PREFIX}{playlist_id}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            logger.info(f"[PlaylistRepository] Redis Cache Hit: Loaded tracks for playlist ID {playlist_id}.")
            return cached

        logger.info(f"[PlaylistRepository] Cache miss: Querying tracks for playlist ID {playlist_id}...")
        raw_tracks = ui_db.get_playlist_tracks(playlist_id)
        cfg = config_manager.load_config()
        folders = config_manager.get_local_sync_folders(cfg)
        audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])
        all_songs = song_scanner.scan_songs_from_paths(folders, audio_exts)
        song_map = {s["filepath"]: s for s in all_songs}

        full_tracks = []
        for rt in raw_tracks:
            fp = rt["filepath"]
            if fp in song_map:
                track_info = dict(song_map[fp])
            else:
                track_info = {
                    "filepath": fp,
                    "filename": os.path.basename(fp),
                    "title": os.path.basename(fp),
                    "artist": "Unknown Artist",
                    "album": "Unknown Album",
                    "duration_formatted": "00:00",
                    "size_formatted": "N/A"
                }
            track_info["track_order"] = rt.get("track_order", 0)
            track_info["added_at"] = rt.get("added_at", "")
            full_tracks.append(track_info)

        self._cache_set(cache_key, full_tracks)
        return full_tracks

    def add_track_to_playlist(self, playlist_id: int, filepath: str) -> bool:
        """
        Add a track to a playlist and invalidate related Redis caches.
        """
        success = ui_db.add_track_to_playlist(playlist_id, filepath)
        if success:
            self._cache_delete(self.CACHE_KEY_PLAYLISTS)
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_TRACKS_PREFIX}{playlist_id}")
        return success

    def remove_track_from_playlist(self, playlist_id: int, filepath: str) -> bool:
        """
        Remove a track from a playlist and invalidate related Redis caches.
        """
        success = ui_db.remove_track_from_playlist(playlist_id, filepath)
        if success:
            self._cache_delete(self.CACHE_KEY_PLAYLISTS)
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_TRACKS_PREFIX}{playlist_id}")
        return success
