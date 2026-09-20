"""
Poweramp Backup & Playlist Importer Module.

Supports:
- Raw SQLite database exports ('lists-export')
- Standard ZIP files (*.zip)
- Extensionless or custom-named ZIP files (*.poweramp-backup, or no extension at all)
- Directory paths containing exported databases

Performs smart multi-tier matching against the local audio library, syncs playlists into SQLite,
and generates a comprehensive Absent Songs Report.
"""
import os
import re
import shutil
import sqlite3
import tempfile
import zipfile
from typing import Dict, List, Any, Optional, Tuple, Set

import ui.db_manager as ui_db
from repositories.playlist_repository import PlaylistRepository
from utils import get_logger

from utils.string import clean_string_for_matching
from model import TrackStatus

logger = get_logger()

ZIP_MAGIC = b"PK\x03\x04"
SQLITE_MAGIC = b"SQLite format 3\x00"


def extract_database_from_source(source: Any) -> Tuple[str, Optional[str]]:
    """
    Extracts or resolves the Poweramp SQLite database from diverse source types:
    - Path string (file, directory, zip with or without extension)
    - File bytes or file-like stream

    Returns:
        (db_path: str, temp_dir: Optional[str])
        Caller should delete temp_dir when finished if not None.
    """
    temp_dir = None

    # 1. If source is a string (filepath or directory)
    if isinstance(source, str):
        path = os.path.abspath(os.path.expanduser(source))
        if not os.path.exists(path):
            raise FileNotFoundError(f"Source file or directory does not exist: {path}")

        # Directory: look for lists-export
        if os.path.isdir(path):
            candidate = os.path.join(path, "lists-export")
            if os.path.isfile(candidate):
                return candidate, None
            # Search immediate children
            for root, _, files in os.walk(path):
                if "lists-export" in files:
                    return os.path.join(root, "lists-export"), None
            raise ValueError(f"No 'lists-export' database found inside directory: {path}")

        # File path: check header
        with open(path, "rb") as f:
            header = f.read(16)

        if header.startswith(ZIP_MAGIC) or zipfile.is_zipfile(path):
            temp_dir = tempfile.mkdtemp(prefix="poweramp_import_")
            with zipfile.ZipFile(path, "r") as z:
                # Find lists-export
                target_name = None
                for member in z.namelist():
                    if member == "lists-export" or member.endswith("/lists-export") or "lists-export" in member:
                        target_name = member
                        break
                if not target_name:
                    # Fallback: look for any sqlite file
                    for member in z.namelist():
                        if not member.endswith("/"):
                            data_sample = z.read(member)[:16]
                            if data_sample.startswith(SQLITE_MAGIC):
                                target_name = member
                                break
                if not target_name:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    raise ValueError(f"Zip archive does not contain a Poweramp 'lists-export' database: {path}")

                extracted_path = z.extract(target_name, temp_dir)
                return extracted_path, temp_dir

        if header.startswith(SQLITE_MAGIC):
            return path, None

        # Try opening directly with sqlite3
        try:
            conn = sqlite3.connect(path)
            conn.execute("SELECT 1 FROM sqlite_master LIMIT 1;")
            conn.close()
            return path, None
        except Exception:
            raise ValueError(f"File is neither a valid ZIP archive nor an SQLite database: {path}")

    # 2. If source is bytes or bytearray
    elif isinstance(source, (bytes, bytearray)):
        temp_dir = tempfile.mkdtemp(prefix="poweramp_import_")
        if source.startswith(ZIP_MAGIC):
            import io
            with zipfile.ZipFile(io.BytesIO(source)) as z:
                target_name = None
                for member in z.namelist():
                    if member == "lists-export" or member.endswith("/lists-export") or "lists-export" in member:
                        target_name = member
                        break
                if not target_name:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    raise ValueError("ZIP archive bytes do not contain 'lists-export'")
                extracted_path = z.extract(target_name, temp_dir)
                return extracted_path, temp_dir
        elif source.startswith(SQLITE_MAGIC):
            db_path = os.path.join(temp_dir, "lists-export")
            with open(db_path, "wb") as f:
                f.write(source)
            return db_path, temp_dir
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise ValueError("Uploaded data is neither a valid ZIP archive nor an SQLite database")

    # 3. If source has a .read() method (e.g. werkzeug FileStorage, io.BytesIO)
    elif hasattr(source, "read"):
        content = source.read()
        return extract_database_from_source(content)

    raise TypeError(f"Unsupported source type: {type(source)}")


def parse_poweramp_tables(db_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Reads playlists and tracks from the Poweramp SQLite database.
    Returns:
        (playlists: List[Dict], rated_tracks: List[Dict])
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Validate tables exist
    tables = {r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if "playlists" not in tables or "tracks" not in tables:
        conn.close()
        raise ValueError("Invalid Poweramp database: missing 'playlists' or 'tracks' table.")

    # 1. Fetch playlists
    raw_playlists = cursor.execute("SELECT _id, name FROM playlists ORDER BY _id ASC").fetchall()
    playlists = []

    for pl in raw_playlists:
        pl_id = pl["_id"]
        pl_name = pl["name"].strip()
        # Fetch tracks for this playlist
        raw_tracks = cursor.execute(
            "SELECT _id, path, readable_name, rating FROM tracks WHERE playlist_id = ? ORDER BY _id ASC",
            (pl_id,)
        ).fetchall()

        track_items = []
        for t in raw_tracks:
            track_items.append({
                "id": t["_id"],
                "path": t["path"],
                "readable_name": t["readable_name"] or os.path.basename(t["path"]),
                "rating": t["rating"] or 0
            })

        playlists.append({
            "id": pl_id,
            "name": pl_name,
            "tracks": track_items
        })

    # 2. Fetch rated / liked tracks (rating > 0)
    raw_rated = cursor.execute(
        "SELECT _id, path, readable_name, rating FROM tracks WHERE rating > 0 ORDER BY _id ASC"
    ).fetchall()
    rated_tracks = []
    seen_paths = set()
    for t in raw_rated:
        p = t["path"]
        if p not in seen_paths:
            seen_paths.add(p)
            rated_tracks.append({
                "id": t["_id"],
                "path": p,
                "readable_name": t["readable_name"] or os.path.basename(p),
                "rating": t["rating"]
            })

    conn.close()
    return playlists, rated_tracks


def build_library_matcher_indices(local_songs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Builds lookup tables for fast, multi-tier matching against local library songs.
    """
    by_filepath = {}
    by_filename = {}
    by_name_no_ext = {}
    by_clean_name = {}

    for s in local_songs:
        fp = s.get("filepath") or s.get("_data") or ""
        if not fp:
            continue
        fn = s.get("filename") or os.path.basename(fp)
        title = s.get("title") or ""

        fp_lower = fp.lower()
        fn_lower = fn.lower()
        no_ext = os.path.splitext(fn_lower)[0]

        by_filepath[fp_lower] = s
        by_filename[fn_lower] = s
        if no_ext not in by_name_no_ext:
            by_name_no_ext[no_ext] = s

        clean_fn = clean_string_for_matching(fn)
        if clean_fn and clean_fn not in by_clean_name:
            by_clean_name[clean_fn] = s

        if title:
            clean_t = clean_string_for_matching(title)
            if clean_t and clean_t not in by_clean_name:
                by_clean_name[clean_t] = s

    return {
        "by_filepath": by_filepath,
        "by_filename": by_filename,
        "by_name_no_ext": by_name_no_ext,
        "by_clean_name": by_clean_name
    }


def find_matching_song(track_path: str, readable_name: str, indices: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Attempts multi-tier matching for a Poweramp track against the library indices:
    1. Exact full path match
    2. Exact filename match
    3. Filename without extension match
    4. Clean normalized filename match
    5. Clean normalized readable_name match
    """
    path_lower = track_path.lower()
    fn = os.path.basename(track_path).lower()
    fn_no_ext = os.path.splitext(fn)[0]

    # Tier 1: exact path
    if path_lower in indices["by_filepath"]:
        return indices["by_filepath"][path_lower]

    # Tier 2: exact filename
    if fn in indices["by_filename"]:
        return indices["by_filename"][fn]

    # Tier 3: filename without extension
    if fn_no_ext in indices["by_name_no_ext"]:
        return indices["by_name_no_ext"][fn_no_ext]

    # Tier 4: clean filename
    clean_fn = clean_string_for_matching(fn)
    if clean_fn and clean_fn in indices["by_clean_name"]:
        return indices["by_clean_name"][clean_fn]

    # Tier 5: clean readable name
    if readable_name:
        clean_rn = clean_string_for_matching(readable_name)
        if clean_rn and clean_rn in indices["by_clean_name"]:
            return indices["by_clean_name"][clean_rn]

    return None


def import_poweramp_backup(
    source: Any,
    sync_to_library: bool = True,
    local_songs: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Main entry point for importing a Poweramp backup:
    1. Extracts SQLite DB from file, zip, extensionless zip, or directory.
    2. Parses playlists, tracks, and ratings.
    3. Matches tracks against local song library.
    4. Syncs matched tracks into SQLite playlists (and 'Liked Music').
    5. Compiles detailed report of synced tracks and absent tracks.
    """
    temp_dir = None
    try:
        db_path, temp_dir = extract_database_from_source(source)
        logger.info(f"[PowerampImporter] Extracted database at: {db_path}")

        playlists_data, rated_tracks = parse_poweramp_tables(db_path)
        logger.info(f"[PowerampImporter] Found {len(playlists_data)} playlists and {len(rated_tracks)} rated tracks.")

        # If local_songs not provided, query from central SQLite DB
        if local_songs is None:
            conn = ui_db.get_connection()
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT filepath, filename, title, artist, album FROM local_songs").fetchall()
            local_songs = [dict(r) for r in rows]
            conn.close()

        indices = build_library_matcher_indices(local_songs)

        playlist_repo = PlaylistRepository()
        total_tracks_count = 0
        total_matched_count = 0
        total_absent_count = 0

        playlist_reports = []
        all_absent_songs = []
        unique_absent_keys: Set[str] = set()

        for pl in playlists_data:
            pl_name = pl["name"]
            tracks = pl["tracks"]
            total_tracks_count += len(tracks)

            matched_tracks = []
            absent_tracks = []

            for t in tracks:
                t_path = t["path"]
                t_rname = t["readable_name"]
                match = find_matching_song(t_path, t_rname, indices)

                if match:
                    matched_tracks.append({
                        "poweramp_path": t_path,
                        "readable_name": t_rname,
                        "matched_filepath": match.get("filepath") or match.get("_data"),
                        "title": match.get("title", t_rname),
                        "artist": match.get("artist", "Unknown")
                    })
                    total_matched_count += 1
                else:
                    absent_item = {
                        "playlist_name": pl_name,
                        "filename": os.path.basename(t_path),
                        "readable_name": t_rname,
                        "original_path": t_path
                    }
                    absent_tracks.append(absent_item)
                    all_absent_songs.append(absent_item)
                    total_absent_count += 1
                    unique_absent_keys.add(f"{os.path.basename(t_path).lower()}::{clean_string_for_matching(t_rname)}")

            # Sync matched and absent tracks to database if requested
            synced_playlist_id = None
            if sync_to_library and (matched_tracks or absent_tracks):
                # Find or create playlist
                existing_pls = playlist_repo.get_playlists()
                target_pl = next((p for p in existing_pls if p["name"].strip().lower() == pl_name.lower()), None)
                if not target_pl:
                    created = playlist_repo.create_playlist(pl_name)
                    synced_playlist_id = created["id"] if created else None
                else:
                    synced_playlist_id = target_pl["id"]

                if synced_playlist_id:
                    for m in matched_tracks:
                        playlist_repo.add_track_to_playlist(
                            playlist_id=synced_playlist_id,
                            filepath=m["matched_filepath"],
                            status=TrackStatus.PRESENT.value,
                            original_path=m.get("poweramp_path"),
                            readable_name=m.get("readable_name"),
                            title=m.get("title"),
                            artist=m.get("artist")
                        )
                    for a in absent_tracks:
                        playlist_repo.add_track_to_playlist(
                            playlist_id=synced_playlist_id,
                            filepath=a["original_path"],
                            status=TrackStatus.ABSENT.value,
                            original_path=a["original_path"],
                            readable_name=a.get("readable_name"),
                            title=a.get("readable_name") or a.get("filename")
                        )

            playlist_reports.append({
                "name": pl_name,
                "playlist_id": synced_playlist_id,
                "total_tracks": len(tracks),
                "matched_count": len(matched_tracks),
                "absent_count": len(absent_tracks),
                "matched_tracks": matched_tracks,
                "absent_tracks": absent_tracks
            })

        # Sync top rated tracks into 'Liked Music'
        liked_matched_count = 0
        if sync_to_library and rated_tracks:
            existing_pls = playlist_repo.get_playlists()
            liked_pl = next((p for p in existing_pls if p["name"] == "Liked Music"), None)
            if not liked_pl:
                created = playlist_repo.create_playlist("Liked Music")
                liked_pl_id = created["id"] if created else None
            else:
                liked_pl_id = liked_pl["id"]

            if liked_pl_id:
                for rt in rated_tracks:
                    m = find_matching_song(rt["path"], rt["readable_name"], indices)
                    if m:
                        playlist_repo.add_track_to_playlist(liked_pl_id, m.get("filepath") or m.get("_data"))
                        liked_matched_count += 1

        summary = {
            "status": "success",
            "total_playlists": len(playlists_data),
            "total_tracks": total_tracks_count,
            "matched_tracks_count": total_matched_count,
            "absent_tracks_count": total_absent_count,
            "unique_absent_count": len(unique_absent_keys),
            "liked_tracks_synced": liked_matched_count,
            "playlists": playlist_reports,
            "absent_songs": all_absent_songs
        }
        logger.info(
            f"[PowerampImporter] Import complete: {len(playlists_data)} playlists, "
            f"{total_matched_count} songs matched, {total_absent_count} songs absent."
        )
        return summary

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
