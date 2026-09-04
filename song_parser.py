"""
Module for parsing ADB MediaStore content query outputs into structured Python dictionaries.
"""
import re
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
    "_data"
]

# Regex pattern matching ', key=' where key is one of the known projection keys
FIELD_SPLIT_PATTERN = re.compile(
    r", (?=(?:" + "|".join(re.escape(k) for k in PROJECTION_KEYS) + r")=)"
)

def format_duration(ms_str: Optional[str]) -> str:
    """Format duration in milliseconds to MM:SS or HH:MM:SS format."""
    if not ms_str or ms_str == "NULL":
        return "00:00"
    try:
        ms = int(ms_str)
        seconds = ms // 1000
        minutes = seconds // 60
        secs = seconds % 60
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "00:00"

def format_size(bytes_str: Optional[str]) -> str:
    """Format size in bytes to human readable string (KB, MB, GB)."""
    if not bytes_str or bytes_str == "NULL":
        return "0 B"
    try:
        b = int(bytes_str)
        if b < 1024:
            return f"{b} B"
        elif b < 1024 * 1024:
            return f"{b / 1024:.1f} KB"
        elif b < 1024 * 1024 * 1024:
            return f"{b / (1024 * 1024):.1f} MB"
        else:
            return f"{b / (1024 * 1024 * 1024):.2f} GB"
    except (ValueError, TypeError):
        return "0 B"

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
