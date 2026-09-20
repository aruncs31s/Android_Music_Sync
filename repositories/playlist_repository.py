"""
Playlist Repository module with Redis caching and SQLite database fallback.
"""
import os
from dataclasses import asdict
from typing import List, Dict, Any, Optional

from repositories.base_repository import BaseRepository
import ui.db_manager as ui_db
import utils.config_manager as config_manager
import over_ip.song_scanner as song_scanner
from model import PlaylistRecord, PlaylistTrackRecord, TrackStatus
from utils import get_logger

logger = get_logger()


class PlaylistRepository(BaseRepository):
    """
    Repository for managing playlists and playlist tracks in SQLite (database/db.db)
    with Redis cache-awareness and dataclass models.
    """

    CACHE_KEY_PLAYLISTS = "cache:playlists:all"
    CACHE_KEY_PLAYLIST_TRACKS_PREFIX = "cache:playlists:tracks:"
    CACHE_KEY_PLAYLIST_ABSENT_PREFIX = "cache:playlists:absent:"

    def get_playlists(self) -> List[Dict[str, Any]]:
        """
        Fetch all playlists with track counts, present counts, and absent counts.
        Checks Redis cache first; queries SQLite on cache miss.
        """
        cached = self._cache_get(self.CACHE_KEY_PLAYLISTS)
        if cached is not None:
            logger.info("[PlaylistRepository] Redis Cache Hit: Loaded playlists.")
            return cached

        logger.info("[PlaylistRepository] Cache miss: Querying SQLite database for playlists...")
        raw_playlists = ui_db.get_playlists()
        playlists = [
            PlaylistRecord(
                id=p.get("id"),
                name=p.get("name", ""),
                created_at=p.get("created_at"),
                track_count=p.get("track_count", 0),
                present_count=p.get("present_count", 0),
                absent_count=p.get("absent_count", 0)
            ).to_dict()
            for p in raw_playlists
        ]
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
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_ABSENT_PREFIX}{playlist_id}")
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_ABSENT_PREFIX}all")
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
            fp = rt.get("filepath", "")
            status = rt.get("status") or TrackStatus.PRESENT.value
            orig = rt.get("original_path") or fp
            rname = rt.get("readable_name") or ""

            if status == TrackStatus.PRESENT.value and fp in song_map:
                sm = song_map[fp]
                record = PlaylistTrackRecord(
                    playlist_id=playlist_id,
                    filepath=fp,
                    id=rt.get("id"),
                    original_path=orig,
                    filename=sm.get("filename") or os.path.basename(fp),
                    title=sm.get("title") or rt.get("title") or os.path.basename(fp),
                    artist=sm.get("artist") or rt.get("artist") or "Unknown Artist",
                    album=sm.get("album") or rt.get("album") or "Unknown Album",
                    readable_name=rname,
                    status=TrackStatus.PRESENT.value,
                    track_order=rt.get("track_order", 0),
                    added_at=rt.get("added_at", ""),
                    duration_formatted=sm.get("duration_formatted", "00:00"),
                    size_formatted=sm.get("size_formatted", "N/A")
                )
            elif status == TrackStatus.ABSENT.value:
                record = PlaylistTrackRecord(
                    playlist_id=playlist_id,
                    filepath=fp,
                    id=rt.get("id"),
                    original_path=orig,
                    filename=os.path.basename(orig) if orig else (rname or "Unknown"),
                    title=rt.get("title") or rname or (os.path.basename(orig) if orig else "Unknown"),
                    artist=rt.get("artist") or "Unknown Artist",
                    album=rt.get("album") or "Unknown Album",
                    readable_name=rname,
                    status=TrackStatus.ABSENT.value,
                    track_order=rt.get("track_order", 0),
                    added_at=rt.get("added_at", ""),
                    duration_formatted="N/A",
                    size_formatted="N/A"
                )
            else:
                record = PlaylistTrackRecord(
                    playlist_id=playlist_id,
                    filepath=fp,
                    id=rt.get("id"),
                    original_path=orig,
                    filename=os.path.basename(fp),
                    title=rt.get("title") or os.path.basename(fp),
                    artist=rt.get("artist") or "Unknown Artist",
                    album=rt.get("album") or "Unknown Album",
                    readable_name=rname,
                    status=TrackStatus.PRESENT.value,
                    track_order=rt.get("track_order", 0),
                    added_at=rt.get("added_at", ""),
                    duration_formatted="00:00",
                    size_formatted="N/A"
                )
            full_tracks.append(record.to_dict())

        self._cache_set(cache_key, full_tracks)
        return full_tracks

    def add_track_to_playlist(
        self,
        playlist_id: int,
        filepath: str,
        status: str = TrackStatus.PRESENT.value,
        original_path: Optional[str] = None,
        readable_name: Optional[str] = None,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None
    ) -> bool:
        """
        Add a track to a playlist and invalidate related Redis caches.
        """
        success = ui_db.add_track_to_playlist(
            playlist_id=playlist_id,
            filepath=filepath,
            status=status,
            original_path=original_path,
            readable_name=readable_name,
            title=title,
            artist=artist,
            album=album
        )
        if success:
            self._cache_delete(self.CACHE_KEY_PLAYLISTS)
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_TRACKS_PREFIX}{playlist_id}")
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_ABSENT_PREFIX}{playlist_id}")
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_ABSENT_PREFIX}all")
        return success

    def remove_track_from_playlist(self, playlist_id: int, filepath: str) -> bool:
        """
        Remove a track from a playlist and invalidate related Redis caches.
        """
        success = ui_db.remove_track_from_playlist(playlist_id, filepath)
        if success:
            self._cache_delete(self.CACHE_KEY_PLAYLISTS)
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_TRACKS_PREFIX}{playlist_id}")
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_ABSENT_PREFIX}{playlist_id}")
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_ABSENT_PREFIX}all")
        return success

    def resolve_absent_track(
        self,
        playlist_id: int,
        original_path: str,
        resolved_filepath: str,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        track_id: Optional[int] = None
    ) -> bool:
        """
        Permanently resolve an absent playlist track to a local filepath in SQLite.
        """
        success = ui_db.resolve_playlist_track(
            playlist_id=playlist_id,
            original_path=original_path,
            resolved_filepath=resolved_filepath,
            title=title,
            artist=artist,
            album=album,
            track_id=track_id
        )
        if success:
            self._cache_delete(self.CACHE_KEY_PLAYLISTS)
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_TRACKS_PREFIX}{playlist_id}")
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_ABSENT_PREFIX}{playlist_id}")
            self._cache_delete(f"{self.CACHE_KEY_PLAYLIST_ABSENT_PREFIX}all")
        return success

    def get_absent_tracks(self, playlist_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve absent tracks for a specific playlist or across all playlists.
        """
        cache_key = f"{self.CACHE_KEY_PLAYLIST_ABSENT_PREFIX}{playlist_id if playlist_id is not None else 'all'}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        raw = ui_db.get_playlist_absent_tracks(playlist_id)
        absent = []
        for r in raw:
            orig = r.get("original_path") or r.get("filepath") or ""
            rname = r.get("readable_name") or ""
            rec = PlaylistTrackRecord(
                playlist_id=r.get("playlist_id", 0),
                filepath=r.get("filepath", ""),
                id=r.get("id"),
                original_path=orig,
                filename=os.path.basename(orig) if orig else (rname or "Unknown"),
                title=r.get("title") or rname or (os.path.basename(orig) if orig else "Unknown"),
                artist=r.get("artist") or "Unknown Artist",
                album=r.get("album") or "Unknown Album",
                readable_name=rname,
                status=TrackStatus.ABSENT.value,
                track_order=r.get("track_order", 0),
                added_at=r.get("added_at", ""),
                duration_formatted="N/A",
                size_formatted="N/A"
            )
            d = rec.to_dict()
            d["playlist_name"] = r.get("playlist_name", "")
            absent.append(d)

        self._cache_set(cache_key, absent)
        return absent
