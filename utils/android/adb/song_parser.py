"""
Module for parsing ADB MediaStore content query outputs into structured Python dictionaries.
"""
import os
import re
import datetime
from typing import List, Dict, Any, Optional

PROJECTION_KEYS = [
    "_id",
    "_display_name",
    "title",
    "artist",
    "album",
    "album_artist",
    "composer",
    "track",
    "year",
    "duration",
    "mime_type",
    "_size",
    "_data",
    "date_added",
    "date_modified",
    "bitrate"
]

# Regex pattern matching ', key=' where key is one of the known projection keys
FIELD_SPLIT_PATTERN = re.compile(
    r", (?=(?:" + "|".join(re.escape(k) for k in PROJECTION_KEYS) + r")=)"
)

from utils.time import format_ts as _format_ts, format_duration as _format_duration, format_size as _format_size


def format_timestamp(ts_val: Any) -> str:
    """Format Unix timestamp in seconds to YYYY-MM-DD HH:MM:SS format."""
    return _format_ts(ts_val, default="Unknown")


def format_duration(ms_str: Optional[str]) -> str:
    """Format duration in milliseconds to MM:SS or HH:MM:SS format."""
    return _format_duration(ms_str, is_ms=True)


def format_size(bytes_str: Optional[str]) -> str:
    """Format size in bytes to human readable string (KB, MB, GB)."""
    return _format_size(bytes_str)


def parse_song_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single output line from ADB content query into a song dict.
    Example line:
    Row: 0 _id=641, _display_name=Song.mp3, title=Title, artist=Artist, ...
    """
    line = line.strip()
    if not line or not line.startswith("Row:"):
        return None

    # Strip 'Row: <number> ' prefix
    match = re.match(r"^Row:\s*\d+\s+(.*)$", line)
    if not match:
        return None

    content = match.group(1)
    fields = FIELD_SPLIT_PATTERN.split(content)

    song: Dict[str, Any] = {}

    for field in fields:
        if "=" not in field:
            continue
        key, val = field.split("=", 1)
        key = key.strip()
        val = val.strip()

        # Clean NULL strings
        if val == "NULL":
            val = None

        song[key] = val

    # If title is missing/None, fallback to display name or filename
    if not song.get("title"):
        display_name = song.get("_display_name") or ""
        song["title"] = display_name or "Unknown Title"

    if not song.get("artist"):
        song["artist"] = "Unknown Artist"

    if not song.get("album"):
        song["album"] = "Unknown Album"

    # Add formatted helper fields
    song["duration_formatted"] = format_duration(song.get("duration"))
    song["size_formatted"] = format_size(song.get("_size"))

    # Filepath and Filename
    data_path = song.get("_data") or ""
    display_name = song.get("_display_name") or ""
    song["filepath"] = data_path
    song["filename"] = display_name or os.path.basename(data_path)

    # Modification Time (mtime) and Creation/Added Time (ctime)
    date_mod_raw = song.get("date_modified")
    date_add_raw = song.get("date_added")

    mtime = 0.0
    try:
        if date_mod_raw and str(date_mod_raw).strip() not in ("NULL", "None", ""):
            mtime = float(date_mod_raw)
    except (ValueError, TypeError):
        pass

    ctime = 0.0
    try:
        if date_add_raw and str(date_add_raw).strip() not in ("NULL", "None", ""):
            ctime = float(date_add_raw)
    except (ValueError, TypeError):
        pass

    song["mtime"] = mtime
    song["mtime_str"] = format_timestamp(mtime) if mtime > 0 else "Unknown"
    song["ctime"] = ctime
    song["ctime_str"] = format_timestamp(ctime) if ctime > 0 else "Unknown"

    # Bitrate
    bitrate_val = 0
    bitrate_kbps = "Unknown"
    if song.get("bitrate") and str(song.get("bitrate")).strip() not in ("NULL", "None", ""):
        try:
            bps = int(float(song.get("bitrate")))
            if bps > 0:
                bitrate_val = bps // 1000
                bitrate_kbps = f"{bitrate_val} kbps"
        except Exception:
            pass

    if bitrate_val == 0:
        try:
            dur_ms = int(float(song.get("duration", 0) or 0))
            dur_sec = dur_ms / 1000.0
            sz_bytes = int(float(song.get("_size", 0) or 0))
            if dur_sec > 0 and sz_bytes > 0:
                bitrate_val = int((sz_bytes * 8) / (dur_sec * 1000))
                bitrate_kbps = f"{bitrate_val} kbps"
        except Exception:
            pass

    song["bitrate_val"] = bitrate_val
    song["bitrate_kbps"] = bitrate_kbps

    # Combined searchable string for fast fuzzy matching
    searchable_parts = [
        song.get("title", ""),
        song.get("artist", ""),
        song.get("album", ""),
        song.get("_display_name", ""),
        song.get("_data", "")
    ]
    song["searchable_text"] = " ".join(p for p in searchable_parts if p)

    return song

def parse_songs(lines_or_content) -> List[Dict[str, Any]]:
    """
    Parse multiple lines or raw text output into a list of song dicts.
    """
    if isinstance(lines_or_content, str):
        lines = lines_or_content.splitlines()
    else:
        lines = lines_or_content

    songs = []
    for line in lines:
        parsed = parse_song_line(line)
        if parsed:
            songs.append(parsed)
    return songs
