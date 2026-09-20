"""
Song Repository module with Redis caching and disk fallback.
"""

import datetime
import os
import shutil
import socket
import sys
import threading
import time
from typing import Any, Dict, List, Optional

import audio_metadata
import config_manager
import over_ip.song_scanner as song_scanner
import ui.db_manager as ui_db
import ui.stats_manager as ui_stats
import utils
from model.song import SongRecord
from repositories.base_repository import BaseRepository
from repositories.deleted_song_repository import (
    DeletedSongRepository,
    get_tmp_song_path,
)
from utils import get_logger

logger = get_logger()


class SongRepository(BaseRepository):
    """
    Repository for managing local music library scanning, duplicate detection,
    and song file deletion with Redis caching awareness.
    """

    CACHE_KEY_ALL_SONGS = "cache:songs:all"
    CACHE_KEY_DUPLICATES = "cache:songs:duplicates"

    # Concurrency control: serialize disk scans so concurrent requests
    # do not run multiple heavy disk scans simultaneously, while ensuring
    # callers wait for the active scan rather than returning empty lists.
    _scan_lock = threading.Lock()
    _listeners_lock = threading.Lock()
    _progress_listeners: list[Any] = []
    _last_scan_time: float = 0.0

    def get_all_songs(
        self, force_refresh: bool = False, progress_cb=None
    ) -> list[dict[str, Any]]:
        """
        Fetch all local music library songs sorted by mtime descending.
        Checks Redis/in-memory cache first if enabled.
        When a disk scan is required or in-flight, callers synchronize on _scan_lock
        rather than returning empty results. Any registered progress_cb receives
        live scan progress broadcast from the active scanner thread.
        """
        # Fast path 1: return warm in-memory/Redis cache if not force_refresh
        if not force_refresh:
            cached = self._cache_get(self.CACHE_KEY_ALL_SONGS)
            if cached is not None:
                logger.info("[SongRepository] Cache Hit: Loaded songs library.")
                return cached

            # Fast path 2: load instantaneously from SQLite local_songs table (< 5ms)
            db_songs = ui_db.get_stored_local_songs()
            if db_songs:
                logger.info(
                    f"[SongRepository] SQLite Hit: Loaded {len(db_songs)} songs from local_songs table."
                )
                self._cache_set(self.CACHE_KEY_ALL_SONGS, db_songs)
                return db_songs

        listener_registered = False
        if progress_cb:
            with self._listeners_lock:
                self._progress_listeners.append(progress_cb)
                listener_registered = True

        try:
            with self._scan_lock:
                cached = self._cache_get(self.CACHE_KEY_ALL_SONGS)
                now = time.time()
                # If cached songs exist, and either not force_refresh or scan finished very recently (< 5s ago)
                if cached is not None:
                    if not force_refresh or (
                        now - SongRepository._last_scan_time < 5.0
                    ):
                        logger.info(
                            "[SongRepository] Reusing freshly scanned songs library."
                        )
                        return cached

                if not force_refresh:
                    db_songs = ui_db.get_stored_local_songs()
                    if db_songs:
                        logger.info(
                            f"[SongRepository] SQLite Hit: Loaded {len(db_songs)} songs."
                        )
                        self._cache_set(self.CACHE_KEY_ALL_SONGS, db_songs)
                        return db_songs

                logger.info(
                    "[SongRepository] Cache miss / scan requested: Scanning disk directories..."
                )
                cfg = config_manager.load_config()
                folders = config_manager.get_local_sync_folders(cfg)
                audio_exts = cfg.get(
                    "audio_extensions",
                    [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"],
                )

                def _broadcast_progress(msg: str):
                    with self._listeners_lock:
                        listeners = list(self._progress_listeners)
                    for listener in listeners:
                        try:
                            listener(msg)
                        except Exception:
                            pass

                songs = song_scanner.scan_songs_from_paths(
                    folders, audio_exts, progress_cb=_broadcast_progress
                )

                # Persist scanned songs into SQLite table so subsequent queries load instantaneously
                ui_db.save_local_songs(songs, purge_missing=True)

                self._cache_set(self.CACHE_KEY_ALL_SONGS, songs)
                SongRepository._last_scan_time = time.time()
                return songs
        finally:
            if listener_registered:
                with self._listeners_lock:
                    try:
                        self._progress_listeners.remove(progress_cb)
                    except ValueError:
                        pass

    def get_duplicates(
        self, force_refresh: bool = False, use_fingerprint: bool = False
    ) -> Dict[str, Any]:
        """
        Detect duplicate song clusters across configured music directories.
        Checks Redis cache first if enabled; runs detection algorithm on cache miss.
        """
        cache_key = f"{self.CACHE_KEY_DUPLICATES}:{'fp' if use_fingerprint else 'tag'}"
        if not force_refresh:
            cached = self._cache_get(cache_key)
            if cached is not None:
                logger.info(
                    f"[SongRepository] Redis Cache Hit: Loaded duplicate clusters ({'fingerprint' if use_fingerprint else 'tags'})."
                )
                return cached

        songs = self.get_all_songs(force_refresh=force_refresh)
        dups = ui_stats.detect_duplicate_songs(songs, use_fingerprint=use_fingerprint)

        self._cache_set(cache_key, dups)
        return dups

    def delete_song(self, filepath: str) -> Dict[str, Any]:
        """
        Move an audio file to the repo-local trash folder (tmp/deleted), record its
        metadata (bitrate, ctime/mtime, size) in the deleted songs log, invalidate
        in-memory metadata cache, remove database hide list references, and clear
        Redis song caches. Returns an identical success/error shape as before.
        """
        abs_path = os.path.abspath(filepath)
        if not os.path.exists(abs_path):
            return {
                "status": "error",
                "message": f"File does not exist: {abs_path}",
                "code": 404,
            }

        # Best-effort capture of file stats & technical metadata BEFORE moving.
        record = SongRecord(
            filepath=abs_path,
            filename=os.path.basename(abs_path),
            title=None,
            artist=None,
            album=None,
            bitrate_kbps=None,
            sample_rate_hz=None,
            codec=None,
            size_bytes=None,
            file_created_at=None,
            file_modified_at=None,
        )
        try:
            st = os.stat(abs_path)
            record.size_bytes = st.st_size
            record.file_created_at = utils.format_ts(st.st_ctime)
            record.file_modified_at = utils.format_ts(st.st_mtime)
        except OSError:
            pass

        try:
            meta = audio_metadata.extract_audio_metadata(abs_path)
            record.bitrate_kbps = meta.get("bitrate")
            record.sample_rate_hz = meta.get("sample_rate")
            record.codec = meta.get("codec")
        except Exception:
            pass

        try:
            tmp_path = get_tmp_song_path(abs_path)
            record.tmp_path = tmp_path
            try:
                shutil.move(abs_path, tmp_path)
            except Exception as e:
                logger.error(f"[SongRepository] Failed to move file to trash: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to delete file: {e}",
                    "code": 500,
                }

            # Remove from hide lists if present
            ui_db.remove_hidden_file(abs_path)

            # Invalidate in-memory metadata cache
            audio_metadata.METADATA_CACHE.pop(abs_path, None)

            # Remove from local_songs in SQLite table
            ui_db.delete_stored_local_song(abs_path)

            # Try to log the deletion in the deleted songs log (best-effort).
            try:
                DeletedSongRepository().record_deleted_song(record)
            except Exception as e:
                logger.error(f"[SongRepository] Error recording deleted song log: {e}")

            # Invalidate Redis song caches
            self.invalidate_all_song_caches()

            logger.info(f"[SongRepository] Successfully deleted audio file: {abs_path}")
            return {
                "status": "success",
                "message": f"Successfully deleted {os.path.basename(abs_path)}",
            }
        except Exception as e:
            logger.error(f"[SongRepository] Error deleting song '{abs_path}': {e}")
            return {
                "status": "error",
                "message": f"Failed to delete file: {e}",
                "code": 500,
            }

    def delete_songs_batch(self, filepaths: List[str]) -> Dict[str, Any]:
        """
        Move multiple audio files to repo-local trash (tmp/deleted), record their
        metadata in the deleted songs log, remove from hide lists, and invalidate
        all Redis song caches once after processing the batch.
        """
        if not filepaths:
            return {
                "status": "success",
                "deleted_count": 0,
                "failed": [],
                "message": "No files to delete",
            }

        deleted_count = 0
        failed = []
        deleted_repo = DeletedSongRepository()

        for fp in filepaths:
            abs_path = os.path.abspath(fp)
            if not os.path.exists(abs_path):
                failed.append({"filepath": fp, "error": "File does not exist"})
                continue

            record = SongRecord(
                filepath=abs_path,
                filename=os.path.basename(abs_path),
                title=None,
                artist=None,
                album=None,
                bitrate_kbps=None,
                sample_rate_hz=None,
                codec=None,
                size_bytes=None,
                file_created_at=None,
                file_modified_at=None,
            )
            try:
                st = os.stat(abs_path)
                record.size_bytes = st.st_size
                record.file_created_at = utils.format_ts(st.st_ctime)
                record.file_modified_at = utils.format_ts(st.st_mtime)
            except OSError:
                pass

            try:
                meta = audio_metadata.extract_audio_metadata(abs_path)
                record.bitrate_kbps = meta.get("bitrate")
                record.sample_rate_hz = meta.get("sample_rate")
                record.codec = meta.get("codec")
            except Exception as e:
                logger.warning(
                    f"[SongRepository] Failed to extract metadata for '{abs_path}': {e}"
                )

            try:
                tmp_path = get_tmp_song_path(abs_path)
                record.tmp_path = tmp_path
                shutil.move(abs_path, tmp_path)
                ui_db.remove_hidden_file(abs_path)
                audio_metadata.METADATA_CACHE.pop(abs_path, None)
                ui_db.delete_stored_local_song(abs_path)
                deleted_repo.record_deleted_song(record)
                deleted_count += 1
                logger.info(f"[SongRepository] Batch deleted audio file: {abs_path}")
            except Exception as e:
                logger.error(
                    f"[SongRepository] Failed to delete file in batch '{abs_path}': {e}"
                )
                failed.append({"filepath": fp, "error": str(e)})

        if deleted_count > 0:
            self.invalidate_all_song_caches()

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "failed": failed,
            "message": f"Successfully deleted {deleted_count} files",
        }

    def invalidate_all_song_caches(self):
        """Clear all cached song data in Redis."""
        self._cache_delete(self.CACHE_KEY_ALL_SONGS)
        self._cache_delete(self.CACHE_KEY_DUPLICATES)
        self._cache_delete_pattern(f"{self.CACHE_KEY_DUPLICATES}*")
        SongRepository._last_scan_time = 0.0
        # Clear legacy redis hostname key if present
        try:
            hostname_key = f"over_ip_songs:{socket.gethostname()}"
            self._cache_delete(hostname_key)
        except Exception:
            pass
