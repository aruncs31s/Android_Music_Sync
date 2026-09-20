"""
Music Folder Synchronizer module with high-performance indexing, live progress reporting,
Redis caching, SQLite Hide List & Synced History database filtering, and Ranger-style Dual-Pane TUI (-i) support.

Scans a local music directory, compares files with songs on an ADB device,
separates already-present songs (skipped by default) from missing songs (to sync),
and uploads missing songs to the specified remote destination (/storage/emulated/0/Music/ADB).
"""
import os
import sys
import re
from typing import List, Dict, Any, Tuple, Optional

import utils.android.adb.adb_manager as adb_manager
import utils.android.adb.adb_pusher as adb_pusher
import utils.android.adb.song_parser as song_parser
from utils import fuzzy_matcher, normalize_string
import tui.ranger_sync_tui as ranger_sync_tui
import database.hide_list_db as hide_list_db

from utils import get_logger

logger = get_logger()

DEFAULT_AUDIO_EXTENSIONS = [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"]




def scan_local_music_folder(
    folder_path: str,
    extensions: list[str] |None = None
) -> list[dict[str, str]]:
    """
    Recursively scan a local directory for audio files matching extensions.
    """
    if not extensions:
        extensions = DEFAULT_AUDIO_EXTENSIONS

    ext_set = set(e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions)
    audio_files = []

    if not os.path.exists(folder_path):
        logger.info(f"[Syncer] Local directory '{folder_path}' does not exist.", file=sys.stderr)
        return []

    for root, _, files in os.walk(folder_path):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ext_set:
                full_path = os.path.join(root, f)
                try:
                    size_bytes = os.path.getsize(full_path)
                except OSError:
                    size_bytes = 0
                size_mb = size_bytes / (1024 * 1024)
                audio_files.append({
                    "filename": f,
                    "title_no_ext": os.path.splitext(f)[0],
                    "path": full_path,
                    "rel_path": os.path.relpath(full_path, folder_path),
                    "size_formatted": f"{size_mb:.1f} MB"
                })

    return audio_files


def compare_local_files_with_device(
    local_files: list[dict[str, str]],
    serial: str,
    remote_folder: str = "/storage/emulated/0/Music/ADB",
    redis_cfg: dict[str, Any]  | None= None,
    refresh_cache: bool = False,
    show_hidden: bool = False
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    High-performance comparison of local music files with device contents.
    Includes SQLite Synced History & Hide List filtering, Redis caching, fast lookup, and live progress.
    Returns: (already_present_list, to_sync_list, all_device_songs)
    """
    try:
        raw_songs = adb_manager.query_songs_from_device(serial, redis_cfg=redis_cfg, refresh_cache=refresh_cache)
        device_songs = song_parser.parse_songs(raw_songs)
    except Exception as e:
        logger.info(f"[Syncer] Warning: Failed to query device MediaStore: {e}", file=sys.stderr)
        device_songs = []

    # SQLite Hide List filtering
    if not show_hidden:
        hidden_set = hide_list_db.get_hidden_paths_set()
        local_files = [f for f in local_files if f["path"] not in hidden_set]

    # SQLite Synced Tracks History for this specific device serial
    synced_history_set = hide_list_db.get_synced_paths_set(serial)

    device_norm_map: Dict[str, Dict[str, Any]] = {}
    for song in device_songs:
        title = song.get("title") or ""
        display = song.get("_display_name") or ""
        path = song.get("_data") or ""
        norm_t = normalize_string(title)
        norm_d = normalize_string(display)
        norm_p = normalize_string(os.path.basename(path))

        if norm_t:
            device_norm_map[norm_t] = song
        if norm_d:
            device_norm_map[norm_d] = song
        if norm_p:
            device_norm_map[norm_p] = song

    already_present = []
    to_sync = []
    total = len(local_files)

    for idx, item in enumerate(local_files, 1):
        filename = item["filename"]
        title_no_ext = item["title_no_ext"]
        full_path = item["path"]
        norm_name = normalize_string(title_no_ext)
        norm_file = normalize_string(filename)

        if idx % 25 == 0 or idx == total or idx == 1:
            percent = (idx / total) * 100 if total > 0 else 100.0
            sys.stderr.write(f"\r[Syncer] Checking duplicates: {idx}/{total} ({percent:.1f}%) | Processing: {filename[:40]}...")
            sys.stderr.flush()

        # 1. Check SQLite Synced History first
        if full_path in synced_history_set:
            already_present.append({
                "local": item,
                "device_match": {"title": title_no_ext, "_display_name": filename},
                "match_reason": f"Recorded in SQLite synced history for device [{serial}]"
            })
            continue

        # 2. Check Device Songs Index & Fuzzy Match
        match_found = device_norm_map.get(norm_name) or device_norm_map.get(norm_file)

        if not match_found and len(title_no_ext) > 3:
            matches = fuzzy_matcher.filter_and_rank_songs(title_no_ext, device_songs)
            if matches:
                top_match = matches[0]
                m_title = top_match.get("title") or ""
                m_display = top_match.get("_display_name") or ""
                if title_no_ext.lower() in m_title.lower() or title_no_ext.lower() in m_display.lower():
                    match_found = top_match

        if match_found:
            already_present.append({
                "local": item,
                "device_match": match_found,
                "match_reason": f"Matched: '{match_found.get('title', match_found.get('_display_name'))}' at '{match_found.get('_data')}'"
            })
        else:
            to_sync.append(item)

    sys.stderr.write(f"\r[Syncer] Duplicate check complete! {len(already_present)} existing, {len(to_sync)} missing.              \n")
    sys.stderr.flush()

    return already_present, to_sync, device_songs


def run_sync_workflow(
    local_dir: str,
    device_serial: str |None = None,
    remote_dir: str = "/storage/emulated/0/Music/ADB",
    audio_extensions: list[str]|None = None,
    force_sync: bool = False,
    auto_confirm: bool = False,
    interactive: bool = False,
    redis_cfg: dict[str, Any] |None = None,
    refresh_cache: bool = False,
    show_hidden: bool = False
):
    """
    Main Sync Folder workflow:
    1. Scan local folder with progress indication.
    2. Filter out SQLite hidden files & check SQLite synced tracks history for device serial.
    3. Query target ADB device (using Redis cache if available).
    4. Categorize into (Already Present vs To Sync) with live progress bar.
    5. If interactive (-i), launch Ranger-style Dual-Pane TUI.
    6. Else, prompt or auto-upload missing files to remote_dir.
    7. Broadcast MediaScanner refresh on remote directory.
    """
    logger.info(f"\n======================================================================", file=sys.stderr)
    logger.info(f"                     MUSIC FOLDER SYNCHRONIZER                        ", file=sys.stderr)
    logger.info(f"======================================================================", file=sys.stderr)
    logger.infor.info(f" Local Sync Folder : {os.path.abspath(local_dir)}", file=sys.stderr)
    logger.info(f" Remote Destination: {remote_dir}", file=sys.stderr)

    if not os.path.exists(local_dir):
        logger.info(f"\n[ERROR] Local sync directory '{local_dir}' does not exist.", file=sys.stderr)
        return

    try:
        devices = adb_manager.list_adb_devices()
    except Exception as e:
        logger.info(f"\n[ERROR] Could not list ADB devices: {e}", file=sys.stderr)
        return

    if not devices:
        logger.info("\n[ERROR] No ADB devices connected. Please connect an Android device.", file=sys.stderr)
        return

    target_device = None
    if device_serial:
        for dev in devices:
            if dev["serial"] == device_serial:
                target_device = dev
                break
    if not target_device:
        target_device = devices[0]

    serial = target_device["serial"]
    logger.info(f" Target ADB Device : {target_device['description']}", file=sys.stderr)
    logger.info(f"======================================================================\n", file=sys.stderr)

    logger.info(f"Scanning local music files in '{local_dir}'...", file=sys.stderr)
    local_files = scan_local_music_folder(local_dir, audio_extensions)
    logger.info(f"Found {len(local_files)} local audio files.", file=sys.stderr)

    if not local_files:
        logger.info(f"No audio files found in '{local_dir}'. Nothing to sync.", file=sys.stderr)
        return

    logger.info(f"Querying device music library & comparing local files...", file=sys.stderr)
    already_present, to_sync, device_songs = compare_local_files_with_device(
        local_files, serial, remote_dir, redis_cfg=redis_cfg, refresh_cache=refresh_cache, show_hidden=show_hidden
    )

    if force_sync:
        to_sync_final = local_files
    else:
        to_sync_final = to_sync

    if interactive:
        logger.info("\n[Syncer] Launching Ranger-Style Interactive Sync TUI (-i)...", file=sys.stderr)
        res = ranger_sync_tui.run_ranger_sync_tui(
            to_sync_files=to_sync_final,
            device_songs=device_songs,
            device_serial=serial,
            remote_dir=remote_dir,
            redis_cfg=redis_cfg
        )
        logger.info(f"\n[Syncer] Ranger TUI session finished. Synced {len(res['synced'])} files, Hidden {len(res.get('hidden', []))} files.", file=sys.stderr)
        adb_pusher.refresh_device_media_scanner(serial, remote_dir)
        return

    logger.info(f"\n----------------------------------------------------------------------", file=sys.stderr)
    logger.info(f" [SECTION 1] Already Present / Synced on Device (Skipped by default - {len(already_present)} files):", file=sys.stderr)
    logger.info(f"----------------------------------------------------------------------", file=sys.stderr)
    if not already_present:
        logger.info("  (None found)", file=sys.stderr)
    else:
        display_limit = 15
        for idx, item in enumerate(already_present[:display_limit], 1):
            loc = item["local"]
            reason = item["match_reason"]
            logger.info(f"  {idx:3d}. {loc['filename']} ({loc['size_formatted']})", file=sys.stderr)
            logger.info(f"       -> {reason}", file=sys.stderr)
        if len(already_present) > display_limit:
            logger.info(f"  ... and {len(already_present) - display_limit} more files already present/synced on device.", file=sys.stderr)

    logger.info(f"\n----------------------------------------------------------------------", file=sys.stderr)
    logger.info(f" [SECTION 2] To Sync / Upload ({len(to_sync_final)} files):", file=sys.stderr)
    logger.info(f"----------------------------------------------------------------------", file=sys.stderr)
    if not to_sync_final:
        logger.info("  (No missing files to sync. All local files are already present/synced on device!)", file=sys.stderr)
        logger.info(f"======================================================================\n", file=sys.stderr)
        return

    display_limit_sync = 30
    for idx, item in enumerate(to_sync_final[:display_limit_sync], 1):
        logger.info(f"  {idx:3d}. {item['rel_path']} ({item['size_formatted']})", file=sys.stderr)
    if len(to_sync_final) > display_limit_sync:
        logger.info(f"  ... and {len(to_sync_final) - display_limit_sync} more files to upload.", file=sys.stderr)

    logger.info(f"======================================================================\n", file=sys.stderr)

    should_sync = auto_confirm
    if not should_sync:
        if sys.stdin.isatty() or os.isatty(0):
            try:
                ans = input(f"Proceed to upload {len(to_sync_final)} file(s) to '{remote_dir}' on ADB device? [Y/n]: ").strip().lower()
                should_sync = ans in ("", "y", "yes")
            except (KeyboardInterrupt, EOFError):
                should_sync = False
        else:
            logger.info("Non-interactive mode: Run with --yes or -y to auto-confirm sync.", file=sys.stderr)
            return

    if not should_sync:
        logger.info("Sync cancelled by user.", file=sys.stderr)
        return

    if not adb_pusher.ensure_remote_folder(serial, remote_dir):
        logger.info("[ERROR] Cannot proceed with sync because remote directory could not be prepared.", file=sys.stderr)
        return

    logger.info(f"\nUploading {len(to_sync_final)} file(s) to ADB device...", file=sys.stderr)
    success_count = 0

    for idx, item in enumerate(to_sync_final, 1):
        percent = (idx / len(to_sync_final)) * 100
        logger.info(f"\n[{idx}/{len(to_sync_final)} - {percent:.1f}%] Syncing: {item['filename']}", file=sys.stderr)
        pushed = adb_pusher.push_song_to_device(serial, item["path"], remote_dir, redis_cfg=redis_cfg)
        if pushed:
            success_count += 1

    adb_pusher.refresh_device_media_scanner(serial, remote_dir)

    logger.info(f"\n======================================================================", file=sys.stderr)
    logger.info(f" Sync Complete: {success_count}/{len(to_sync_final)} files uploaded successfully.", file=sys.stderr)
    logger.info(f"======================================================================\n", file=sys.stderr)
