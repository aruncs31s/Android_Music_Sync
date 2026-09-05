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

    for folder in folder_paths:
        if not folder or not os.path.exists(folder):
            continue

        folder_abs = os.path.abspath(folder)

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
                        size = st.st_size
                    except OSError:
                        mtime = 0.0
                        size = 0

                    meta = audio_metadata.extract_audio_metadata(full_path)

                    filename = os.path.basename(full_path)
                    title = meta.get("title") or os.path.splitext(filename)[0]
                    artist = meta.get("artist") or "Unknown"
                    album = meta.get("album") or "Unknown"

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
                        "duration_sec": 0.0,
                        "duration_formatted": meta.get("duration", "00:00"),
                        "bitrate_kbps": meta.get("bitrate", "Unknown"),
                        "sample_rate_hz": meta.get("sample_rate", "Unknown"),
                        "channels": meta.get("channels", "Stereo"),
                        "codec": meta.get("codec", ext.lstrip(".")),
                        "searchable_text": f"{title} {artist} {album} {filename}".lower()
                    }
                    songs.append(song)

    # Sort songs by mtime descending (newest modified files first)
    songs.sort(key=lambda s: s.get("mtime", 0.0), reverse=True)

    # Re-index _id sequentially
    for idx, s in enumerate(songs, 1):
        s["_id"] = idx

    return songs
