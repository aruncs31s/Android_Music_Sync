"""
Deleted Song Repository module with Redis caching and SQLite fallback.
Files deleted from the music library are moved to a repo-local trash folder
(tmp/deleted) so they can be restored later.
"""

import os
import shutil
import time
from typing import Any, Dict, List, Optional

from repositories.exceptions import TrashFileMissingError, FileMoveError
import audio_metadata
import ui.db_manager as ui_db
from model.song import RestoredSongRecord, SongRecord
from over_ip.song_scanner import format_mtime
from repositories.base_repository import BaseRepository
from utils import get_logger

logger = get_logger()

TRASH_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tmp", "deleted"
)


def get_tmp_song_path(filepath: str) -> str:
    """Build a unique trash path for a file being deleted."""
    os.makedirs(TRASH_ROOT, exist_ok=True)
    basename = os.path.basename(filepath)
    unique = f"{int(time.time() * 1000)}_{basename}"
    return os.path.join(TRASH_ROOT, unique)


class DeletedSongRepository(BaseRepository):
    """
    Repository for managing deleted song records in database/db.db with Redis caching.
    """

    CACHE_KEY_DELETED = "cache:songs:deleted"

    def get_deleted_songs(self) -> List[Dict[str, Any]]:
        """
        Fetch all deleted song records.
        Checks Redis cache first; queries SQLite database on cache miss.
        """
        cached = self._cache_get(self.CACHE_KEY_DELETED)
        if cached is not None:
            logger.info(
                "[DeletedSongRepository] Redis Cache Hit: Loaded deleted songs."
            )
            return cached

        records = ui_db.get_deleted_songs()
        self._cache_set(self.CACHE_KEY_DELETED, records)
        return records

    def record_deleted_song(self, record: SongRecord) -> bool:
        """
        Persist a deleted song record and invalidate Redis deleted-songs cache.
        """
        success = ui_db.add_deleted_song(record)
        if success:
            self._cache_delete(self.CACHE_KEY_DELETED)
        return success

    def restore_deleted_song(self, record_id: int) -> dict[str, Any]:
        """
        Move a deleted song back to its original filepath and remove its record.
        Returns a result dict with status and message.
        """
        record = None
        try:
            for r in ui_db.get_deleted_songs():
                if r["id"] == record_id:
                    record = r
                    break
        except Exception as e:
            logger.error(
                f"[DeletedSongRepository] Error fetching record {record_id}: {e}"
            )
            return {"status": "error", "message": f"Failed to locate record: {e}"}

        if not record:
            return {
                "status": "error",
                "message": f"Deleted song record {record_id} not found",
                "code": 404,
            }

        tmp_path = record.get("tmp_path")
        filepath = record.get("filepath")
        if not tmp_path or not os.path.isfile(tmp_path):
            ui_db.remove_deleted_song(record_id)
            self._cache_delete(self.CACHE_KEY_DELETED)
            return {
                "status": "error",
                "message": f"Trash file missing: {tmp_path}",
                "code": 404,
            }

        try:
            parent = os.path.dirname(filepath)
            if parent:
                os.makedirs(parent, exist_ok=True)
            shutil.move(tmp_path, filepath)
        except Exception as e:
            logger.error(
                f"[DeletedSongRepository] Error restoring file to '{filepath}': {e}"
            )
            return {
                "status": "error",
                "message": f"Failed to restore file: {e}",
                "code": 500,
            }

        if not ui_db.remove_deleted_song(record_id):
            logger.warning(
                f"[DeletedSongRepository] Restored file but failed to remove record {record_id}."
            )

        # Re-index restored song into SQLite local_songs table
        try:
            st = os.stat(filepath)
            meta = audio_metadata.extract_audio_metadata(filepath)
            filename = os.path.basename(filepath)
            title = meta.get("title") or os.path.splitext(filename)[0]
            artist = meta.get("artist") or "Unknown"
            album = meta.get("album") or "Unknown"
            bitrate_str = meta.get("bitrate", "Unknown")
            bitrate_val = 0
            try:
                if "kbps" in str(bitrate_str):
                    bitrate_val = int(str(bitrate_str).replace("kbps", "").strip())
            except Exception:
                logger.warning(
                    f"[DeletedSongRepository] Failed to parse bitrate '{bitrate_str}' for {filepath}"
                )

            restored_song_record = RestoredSongRecord(
                filepath=filepath,
                filename=filename,
                title=title,
                artist=artist,
                album=album,
                size_bytes=st.st_size,
                file_created_at=format_mtime(getattr(st, "st_birthtime", st.st_ctime)),
                file_modified_at=format_mtime(st.st_mtime),
                duration_sec=meta.get("duration_sec", 0.0),
                duration_formatted=meta.get("duration", "00:00"),
                bitrate_kbps=bitrate_str,
                bitrate_val=bitrate_val,
                sample_rate_hz=meta.get("sample_rate", "Unknown"),
                channels=meta.get("channels", "Stereo"),
                codec=meta.get("codec", os.path.splitext(filename)[1].lstrip(".")),
                searchable_text=f"{title} {artist} {album} {filename}".lower(),
            )
            ui_db.save_local_songs([restored_song_record], purge_missing=False)
        except (TrashFileMissingError, FileMoveError) as e:
            return {
                "status": "error",
                "message": str(e),
                "code": e.code,
            }

        self._cache_delete(self.CACHE_KEY_DELETED)
        self._cache_delete("cache:songs:all")
        self._cache_delete("cache:songs:duplicates")
        logger.info(f"[DeletedSongRepository] Restored deleted song: {filepath}")

        return {
            "status": "success",
            "message": f"Restored {os.path.basename(filepath)}",
            "filepath": filepath,
        }

    def clear_deleted_history(self) -> dict[str, Any]:
        """
        Permanently remove all trash files and clear deleted song records.
        """
        removed = 0
        failed = 0
        for r in self.get_deleted_songs():
            tmp_path = r.get("tmp_path")
            if tmp_path and os.path.isfile(tmp_path):
                try:
                    os.remove(tmp_path)
                    removed += 1
                except Exception as e:
                    logger.error(
                        f"[DeletedSongRepository] Error removing trash file '{tmp_path}': {e}"
                    )
                    failed += 1

        cleared = ui_db.clear_deleted_songs()
        self._cache_delete(self.CACHE_KEY_DELETED)
        return {
            "status": "success",
            "message": f"Cleared deleted songs history ({removed} file(s) removed).",
            "removed": removed,
            "failed": failed,
            "records_cleared": cleared,
        }
