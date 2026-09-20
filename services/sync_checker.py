"""
Sync Checker Module.
Checks if a specific local song exists on a destination device (ADB or Over-IP peer),
and identifies similar songs using fuzzy matching and audio metadata comparison.
"""

import os
import re
from typing import Any

from utils import audio_metadata, fuzzy_matcher
import database.hide_list_db as hide_list_db
from repositories import device_repo, song_repo
from utils import get_logger
from utils import normalize_string as normalize_str

logger = get_logger()


def get_local_song_details(filepath: str) -> dict[str, Any]:
    """Retrieve or extract metadata for a local song file."""
    abs_path = os.path.abspath(filepath)
    filename = os.path.basename(abs_path)
    title_no_ext = os.path.splitext(filename)[0]

    # Try lookup in song_repo cache first
    try:
        all_songs = song_repo.get_all_songs()
        for s in all_songs:
            if os.path.abspath(s.get("filepath", "")) == abs_path:
                return {
                    "filepath": abs_path,
                    "filename": filename,
                    "title": s.get("title") or title_no_ext,
                    "artist": s.get("artist") or "Unknown",
                    "album": s.get("album") or "Unknown",
                    "duration_formatted": s.get("duration_formatted") or "00:00",
                    "size_formatted": s.get("size_formatted") or "0 B",
                    "bitrate_kbps": s.get("bitrate_kbps") or "Unknown",
                    "mtime_str": s.get("mtime_str") or "Unknown",
                }
    except Exception as e:
        logger.info(f"err {e}")

    # Fallback to direct extraction
    meta = audio_metadata.extract_audio_metadata(abs_path)
    return {
        "filepath": abs_path,
        "filename": filename,
        "title": title_no_ext,
        "artist": "Unknown",
        "album": "Unknown",
        "duration_formatted": meta.get("duration", "00:00"),
        "size_formatted": meta.get("size", "0 B"),
        "bitrate_kbps": meta.get("bitrate", "Unknown"),
        "mtime_str": "Unknown",
    }


def calculate_similarity_score(
    local_song: dict[str, Any], dev_song: dict[str, Any]
) -> int:
    """
    Calculate an intuitive 0-100% similarity score between a local song and a device song
    based on title, artist, and filename.
    """
    l_title = normalize_str(local_song.get("title", ""))
    d_title = normalize_str(dev_song.get("title", ""))
    l_file = normalize_str(local_song.get("filename", ""))
    d_file = normalize_str(
        dev_song.get("_display_name")
        or dev_song.get("filename")
        or os.path.basename(dev_song.get("_data", ""))
    )

    if l_title and l_title == d_title:
        return 100
    if l_file and l_file == d_file:
        return 100

    score = 0
    # Title substring or sequence check
    if l_title and d_title:
        if l_title in d_title or d_title in l_title:
            ratio = min(len(l_title), len(d_title)) / max(len(l_title), len(d_title))
            score = max(score, int(70 + (ratio * 25)))
        else:
            matched, raw_score, _ = fuzzy_matcher.fuzzy_subsequence_match(
                l_title[:15], d_title
            )
            if matched:
                score = max(score, min(85, 50 + int(raw_score / 3)))

    # Artist match check bonus
    l_artist = normalize_str(local_song.get("artist", ""))
    d_artist = normalize_str(dev_song.get("artist", ""))
    if l_artist and d_artist and l_artist != "unknown" and d_artist != "unknown":
        if l_artist == d_artist:
            score = min(98, score + 15)
        elif l_artist in d_artist or d_artist in l_artist:
            score = min(95, score + 10)

    return max(10, min(99, score))


def format_device_song(dev_song: dict[str, Any]) -> dict[str, Any]:
    """Format a device song dictionary into a clean client-facing structure."""
    display_name = (
        dev_song.get("_display_name")
        or dev_song.get("filename")
        or os.path.basename(dev_song.get("_data", ""))
    )
    return {
        "id": dev_song.get("_id") or dev_song.get("id"),
        "title": dev_song.get("title") or display_name,
        "artist": dev_song.get("artist") or "Unknown",
        "album": dev_song.get("album") or "Unknown",
        "filename": display_name,
        "filepath": dev_song.get("_data") or dev_song.get("filepath") or "",
        "duration_formatted": dev_song.get("duration_formatted") or "00:00",
        "size_formatted": dev_song.get("size_formatted") or "0 B",
        "bitrate_kbps": dev_song.get("bitrate_kbps") or "Unknown",
    }


def check_song_on_device(filepath: str, device_id: str) -> Dict[str, Any]:
    """
    Check if a specific local song exists on the selected destination device,
    and find similar tracks.
    """
    if not filepath or not os.path.exists(filepath):
        return {
            "status": "error",
            "message": f"Local file not found: {filepath}",
            "code": 404,
        }

    local_song = get_local_song_details(filepath)
    local_filename = local_song["filename"]
    local_title = local_song["title"]
    local_artist = local_song["artist"]

    norm_local_file = normalize_str(local_filename)
    norm_local_title = normalize_str(local_title)
    norm_local_artist = normalize_str(local_artist)

    # 1. Fetch destination device songs
    try:
        device_data = device_repo.get_device_songs(device_id, force_refresh=False)
    except Exception as e:
        logger.error(f"[SyncChecker] Error fetching songs for {device_id}: {e}")
        return {
            "status": "error",
            "message": f"Failed to query destination device: {e}",
            "code": 500,
        }

    device_name = device_data.get("device_name") or device_id
    device_type = device_data.get("device_type") or "Connected Device"
    device_songs: list[dict[str, Any]] = device_data.get("songs") or []

    # Check SQLite synced history if ADB serial
    is_in_synced_history = False
    synced_match_reason = ""
    if device_id.startswith("adb_") or device_id.startswith("adb:"):
        serial = (
            device_id.split("_", 1)[-1]
            if "_" in device_id
            else device_id.split(":", 1)[-1]
        )
        synced_set = hide_list_db.get_synced_paths_set(serial)
        if os.path.abspath(filepath) in synced_set:
            is_in_synced_history = True
            synced_match_reason = (
                f"Recorded in SQLite synced history for device [{serial}]"
            )

    exact_match: dict[str, Any] | None = None
    exact_match_reason = ""
    exact_match_id = None

    # 2. Check for Exact Match
    for song in device_songs:
        dev_file = (
            song.get("_display_name")
            or song.get("filename")
            or os.path.basename(song.get("_data", ""))
        )
        dev_title = song.get("title") or ""
        dev_artist = song.get("artist") or ""

        norm_dev_file = normalize_str(dev_file)
        norm_dev_title = normalize_str(dev_title)
        norm_dev_artist = normalize_str(dev_artist)

        # Match 1: Exact Filename
        if norm_local_file and norm_local_file == norm_dev_file:
            exact_match = format_device_song(song)
            exact_match_reason = f"Identical filename on destination ({dev_file})"
            exact_match_id = song.get("_id") or song.get("id")
            break

        # Match 2: Matching title + artist
        if norm_local_title and norm_dev_title and norm_local_title == norm_dev_title:
            if (
                not norm_local_artist
                or norm_local_artist == "unknown"
                or norm_local_artist == norm_dev_artist
            ):
                exact_match = format_device_song(song)
                exact_match_reason = f"Identical Title & Artist on destination"
                exact_match_id = song.get("_id") or song.get("id")
                break

    # If not found in live media, but recorded in synced history
    if not exact_match and is_in_synced_history:
        exact_match = {
            "title": local_title,
            "artist": local_artist,
            "album": local_song.get("album", ""),
            "filename": local_filename,
            "filepath": "Recorded in synced history",
            "duration_formatted": local_song.get("duration_formatted", ""),
            "size_formatted": local_song.get("size_formatted", ""),
            "bitrate_kbps": local_song.get("bitrate_kbps", ""),
        }
        exact_match_reason = synced_match_reason

    # 3. Find Similar Songs on Destination Device
    similar_songs: list[dict[str, Any]] = []
    seen_similar_ids = set()

    # Exclude the exact match if found
    if exact_match_id:
        seen_similar_ids.add(str(exact_match_id))

    # Search query using title (clean punctuation / words)
    clean_query = re.sub(r"[\(\)\[\]_\-]", " ", local_title).strip()
    ranked_candidates = fuzzy_matcher.filter_and_rank_songs(clean_query, device_songs)

    for cand in ranked_candidates:
        cand_id = str(
            cand.get("_id")
            or cand.get("id")
            or cand.get("_data")
            or cand.get("filepath")
        )
        if cand_id in seen_similar_ids:
            continue

        dev_title = cand.get("title") or ""
        norm_cand_title = normalize_str(dev_title)

        # Skip if it's the exact same title as the exact match
        if exact_match and norm_cand_title == norm_local_title:
            continue

        sim_score = calculate_similarity_score(local_song, cand)
        if sim_score < 40:
            continue

        seen_similar_ids.add(cand_id)
        fmt = format_device_song(cand)
        fmt["similarity_score"] = sim_score

        # Comparison annotations
        notes = []
        l_bitrate = local_song.get("bitrate_kbps")
        d_bitrate = fmt.get("bitrate_kbps")
        if (
            l_bitrate
            and d_bitrate
            and str(l_bitrate) != "Unknown"
            and str(d_bitrate) != "Unknown"
        ):
            if str(l_bitrate) != str(d_bitrate):
                notes.append(
                    f"Bitrate: Local {l_bitrate} kbps vs Device {d_bitrate} kbps"
                )
            else:
                notes.append(f"Same bitrate ({l_bitrate} kbps)")

        l_dur = local_song.get("duration_formatted")
        d_dur = fmt.get("duration_formatted")
        if l_dur and d_dur and l_dur != "00:00" and d_dur != "00:00":
            if l_dur != d_dur:
                notes.append(f"Duration: Local {l_dur} vs Device {d_dur}")

        fmt["comparison_note"] = (
            " | ".join(notes) if notes else "Similar title or artist"
        )
        similar_songs.append(fmt)

        if len(similar_songs) >= 5:
            break

    # Sort similar songs by similarity score descending
    similar_songs.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "status": "success",
        "device_id": device_id,
        "device_name": device_name,
        "device_type": device_type,
        "local_song": local_song,
        "exact_match": {
            "found": exact_match is not None,
            "match_reason": exact_match_reason,
            "device_song": exact_match,
        },
        "similar_songs": similar_songs,
    }
