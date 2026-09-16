"""
Multi-Folder Song Scanner for Over-IP HTTP Synchronization.
Scans multiple configured folder paths recursively, extracts audio metadata,
and sorts results by file modification timestamp (mtime descending / newest first).
"""
import os
import time
import datetime
from typing import List, Dict, Any

import audio_metadata
from utils import get_logger

logger = get_logger()


def format_mtime(ts: float) -> str:
    """Format Unix timestamp as ISO-like date string."""
    try:
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def scan_songs_from_paths(
    folder_paths: List[str],
    audio_extensions: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Recursively scan a list of local folder paths for audio files.
    Returns list of song dictionaries sorted by modification time (mtime descending).
    """
    if audio_extensions is None:
        audio_extensions = [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"]

    valid_extensions = set(ext.lower() for ext in audio_extensions)
    songs: List[Dict[str, Any]] = []

    seen_paths = set()
    logger.info(f"Starting song library scan across {len(folder_paths)} configured paths...")

    for folder in folder_paths:
        if not folder or not os.path.exists(folder):
            logger.warning(f"Scan path skipped (does not exist): '{folder}'")
            continue

        folder_abs = os.path.abspath(folder)
        logger.info(f"Scanning directory: '{folder_abs}'...")
        scanned_in_folder = 0

        for root, _, files in os.walk(folder_abs):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_extensions:
                    full_path = os.path.join(root, file)
                    if full_path in seen_paths:
                        continue
                    seen_paths.add(full_path)

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

                    meta = audio_metadata.extract_audio_metadata(full_path)

                    filename = os.path.basename(full_path)
                    title = meta.get("title") or os.path.splitext(filename)[0]
                    artist = meta.get("artist") or "Unknown"
                    album = meta.get("album") or "Unknown"

                    bitrate_str = meta.get("bitrate", "Unknown")
                    bitrate_val = 0
                    try:
                        if "kbps" in str(bitrate_str):
                            bitrate_val = int(str(bitrate_str).replace("kbps", "").strip())
                    except Exception:
                        bitrate_val = 0

                    song = {
                        "_id": len(songs) + 1,
                        "title": title,
                        "artist": artist,
                        "album": album,
                        "_data": full_path,
                        "filepath": full_path,
                        "filename": filename,
                        "size": size,
                        "size_formatted": meta.get("size", f"{size / (1024*1024):.1f} MB"),
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
                        "searchable_text": f"{title} {artist} {album} {filename}".lower()
                    }
                    songs.append(song)
                    scanned_in_folder += 1

        logger.info(f"Finished scanning '{folder_abs}': Found {scanned_in_folder} audio files.")

    # Sort songs by mtime descending (newest modified files first)
    songs.sort(key=lambda s: s.get("mtime", 0.0), reverse=True)

    # Re-index _id sequentially
    for idx, s in enumerate(songs, 1):
        s["_id"] = idx

    logger.info(f"Scan complete. Total songs loaded & sorted by mtime: {len(songs)}")
    return songs
