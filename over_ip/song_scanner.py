"""
Multi-Folder Song Scanner for Over-IP HTTP Synchronization.
Scans multiple configured folder paths recursively, extracts audio metadata,
and sorts results by file modification timestamp (mtime descending / newest first).
"""

import datetime
import os
from typing import Any

import audio_metadata
from utils import get_logger

logger = get_logger()

# Emit at most one progress line per this many files to avoid flooding the
# SSE client with per-file events (which froze the browser during large scans).
PROGRESS_EVERY = 25


def format_mtime(ts: float) -> str:
    """Format Unix timestamp as ISO-like date string."""
    try:
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def scan_songs_from_paths(
    folder_paths: list[str],
    audio_extensions: list[str] = None,
    progress_cb=None,
    existing_metadata_map: dict[str, dict[str, Any]] |None = None,
) -> list[dict[str, Any]]:
    """
    Recursively scan a list of local folder paths for audio files.
    Returns list of song dictionaries sorted by modification time (mtime descending).
    Optional progress_cb(msg: str) reports files as they are discovered.
    If existing_metadata_map is provided (or loaded from SQLite), unchanged files
    (matching mtime & size) reuse cached metadata without slow mutagen disk parsing.
    """
    if audio_extensions is None:
        audio_extensions = [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"]

    if existing_metadata_map is None:
        try:
            import database.db_manager as central_db

            stored = central_db.get_stored_local_songs()
            if stored:
                existing_metadata_map = {s["filepath"]: s for s in stored}
        except Exception:
            existing_metadata_map = None

    valid_extensions = set(ext.lower() for ext in audio_extensions)
    songs: list[dict[str, Any]] = []

    seen_paths = set()
    logger.info(
        f"Starting song library scan across {len(folder_paths)} configured paths..."
    )

    for folder in folder_paths:
        if not folder or not os.path.exists(folder):
            logger.warning(f"Scan path skipped (does not exist): '{folder}'")
            if progress_cb:
                try:
                    progress_cb(f"[WARN] Directory not found: '{folder}'")
                except Exception:
                    pass
            continue

        folder_abs = os.path.abspath(folder)
        logger.info(f"Scanning directory: '{folder_abs}'...")
        if progress_cb:
            try:
                progress_cb(f"[INFO] Scanning directory: {folder_abs}")
            except Exception:
                pass
        scanned_in_folder = 0

        def _on_walk_error(err):
            logger.warning(f"[SongScanner] Cannot access '{err.filename}': {err}")
            if progress_cb:
                try:
                    progress_cb(f"[WARN] Permission/access error: {err.filename}")
                except Exception:
                    pass

        for root, _, files in os.walk(folder_abs, onerror=_on_walk_error):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_extensions:
                    full_path = os.path.join(root, file)
                    if full_path in seen_paths:
                        continue
                    seen_paths.add(full_path)
                    scanned_in_folder += 1

                    try:
                        st = os.stat(full_path)
                        mtime = st.st_mtime
                        ctime = getattr(st, "st_birthtime", st.st_ctime)
                        size = st.st_size
                    except OSError as err:
                        logger.error(f"Failed stat for file '{full_path}': {err}")
                        mtime = 0.0
                        ctime = 0.0
                        size = 0

                    # Fast path: if file mtime and size are unchanged in SQLite, reuse metadata
                    if existing_metadata_map and full_path in existing_metadata_map:
                        existing = existing_metadata_map[full_path]
                        if (
                            abs(existing.get("mtime", 0.0) - mtime) < 0.01
                            and existing.get("size") == size
                        ):
                            song = dict(existing)
                            song["_id"] = len(songs) + 1
                            songs.append(song)
                            if progress_cb and len(songs) % PROGRESS_EVERY == 0:
                                try:
                                    progress_cb(
                                        f"[SCAN] Indexed {len(songs)} audio files (verified: {file})..."
                                    )
                                except Exception as e:
                                    logger.warn(f"Error occurred while updating progress: {e}")
                            continue

                    meta = audio_metadata.extract_audio_metadata(full_path)

                    filename = os.path.basename(full_path)
                    title = meta.get("title") or os.path.splitext(filename)[0]
                    artist = meta.get("artist") or "Unknown"
                    album = meta.get("album") or "Unknown"

                    bitrate_str = meta.get("bitrate", "Unknown")
                    bitrate_val = 0
                    try:
                        if "kbps" in str(bitrate_str):
                            bitrate_val = int(
                                str(bitrate_str).replace("kbps", "").strip()
                            )
                    except Exception:
                        bitrate_val = 0
                    logger.debug(
                        f"Scanned file: {full_path} | Title: {title} | Artist: {artist} | Album: {album} | Size: {size} bytes | MTime: {mtime} | CTime: {ctime}"
                    )
                    song = {
                        "_id": len(songs) + 1,
                        "title": title,
                        "artist": artist,
                        "album": album,
                        "_data": full_path,
                        "filepath": full_path,
                        "filename": filename,
                        "size": size,
                        "size_formatted": meta.get(
                            "size", f"{size / (1024 * 1024):.1f} MB"
                        ),
                        "mtime": mtime,
                        "mtime_str": format_mtime(mtime),
                        "ctime": ctime,
                        "ctime_str": format_mtime(ctime),
                        "duration_sec": 0.0,
                        "duration_formatted": meta.get("duration", "00:00"),
                        "bitrate_kbps": bitrate_str,
                        "bitrate_val": bitrate_val,
                        "sample_rate_hz": meta.get("sample_rate", "Unknown"),
                        "channels": meta.get("channels", "Stereo"),
                        "codec": meta.get("codec", ext.lstrip(".")),
                        "searchable_text": f"{title} {artist} {album} {filename}".lower(),
                    }
                    songs.append(song)

                    if progress_cb and len(songs) % PROGRESS_EVERY == 0:
                        try:
                            progress_cb(
                                f"[SCAN] Scanned {len(songs)} audio files (current: {filename})..."
                            )
                        except Exception:
                            pass

        logger.info(
            f"Finished scanning '{folder_abs}': Found {scanned_in_folder} audio files."
        )
        if progress_cb:
            try:
                progress_cb(
                    f"[SCAN]  Finished folder: {folder_abs} — {scanned_in_folder} audio files."
                )
            except Exception:
                pass

    # Sort songs by mtime descending (newest modified files first)
    songs.sort(key=lambda s: s.get("mtime", 0.0), reverse=True)

    # Re-index _id sequentially
    for idx, s in enumerate(songs, 1):
        s["_id"] = idx

    logger.info(f"Scan complete. Total songs loaded & sorted by mtime: {len(songs)}")
    if progress_cb:
        try:
            progress_cb(f"[SCAN]  Scan complete — {len(songs)} audio files loaded.")
        except Exception:
            pass
    return songs
