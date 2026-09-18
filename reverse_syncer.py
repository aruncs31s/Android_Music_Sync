"""
Reverse Synchronization Module (ADB Device -> Local Directory) with Redis caching,
SQLite Hide List database filtering, and Ranger TUI support.

Queries songs present on connected ADB device, compares with local music folder (/home/aruncs/Music),
identifies songs on the device that do not exist locally, and pulls them via ADB.
"""
import os
import subprocess
import re
from typing import List, Dict, Any, Tuple, Optional

import adb_manager
import song_parser
import syncer
import fuzzy_matcher
import redis_cache
import ranger_reverse_sync_tui
import hide_list_db
from utils import get_logger
logger = get_logger()


def normalize_string(s: str) -> str:
    """Normalize string for fast comparison (lowercase, alphanumeric only)."""
    return re.sub(r"[^a-zA-Z0-9]", "", s.lower())


def get_local_music_files(
    local_dir: str,
    audio_extensions: List[str] = None,
    redis_cfg: Optional[Dict[str, Any]] = None,
    refresh_cache: bool = False
) -> List[Dict[str, str]]:
    """
    Get local music files using Redis cache if available, falling back to disk scan.
    """
    if not refresh_cache and redis_cfg:
        cached_files = redis_cache.get_cached_local_index(local_dir, redis_cfg)
        if cached_files is not None:
            return cached_files

    local_files = syncer.scan_local_music_folder(local_dir, audio_extensions)

    if redis_cfg and local_files:
        redis_cache.set_cached_local_index(local_dir, local_files, redis_cfg)

    return local_files


def compare_device_with_local(
    device_songs: List[Dict[str, Any]],
    local_files: List[Dict[str, str]],
    show_hidden: bool = False
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Compare device songs with local files.
    Includes SQLite Hide List filtering.
    Returns: (already_local_list, missing_locally_list)
    """
    hidden_set = hide_list_db.get_hidden_paths_set() if not show_hidden else set()

    local_norm_set = set()
    for f in local_files:
        local_norm_set.add(normalize_string(f["title_no_ext"]))
        local_norm_set.add(normalize_string(f["filename"]))

    already_local = []
    missing_locally = []

    for song in device_songs:
        title = song.get("title") or ""
        display = song.get("_display_name") or ""
        remote_path = song.get("_data") or ""

        # Skip if remote path or title is in SQLite hide list
        if not show_hidden:
            if remote_path in hidden_set or title in hidden_set or display in hidden_set:
                continue

        norm_t = normalize_string(title)
        norm_d = normalize_string(display)
        norm_p = normalize_string(os.path.basename(remote_path))

        if norm_t in local_norm_set or norm_d in local_norm_set or norm_p in local_norm_set:
            already_local.append(song)
        else:
            missing_locally.append(song)

    return already_local, missing_locally


def run_reverse_sync_workflow(
    local_dir: str,
    device_serial: Optional[str] = None,
    audio_extensions: List[str] = None,
    auto_confirm: bool = False,
    interactive: bool = False,
    redis_cfg: Optional[Dict[str, Any]] = None,
    refresh_cache: bool = False,
    show_hidden: bool = False
):
    """
    Main Reverse Sync workflow:
    1. Select ADB device.
    2. Query device MediaStore songs (fully cached in Redis).
    3. Scan local folder (/home/aruncs/Music) (fully cached in Redis).
    4. Filter out SQLite hidden files unless show_hidden=True.
    5. Categorize songs into Already Local vs Missing Locally.
    6. If interactive (-i), launch Ranger-style Dual-Pane Reverse Sync TUI (with 'h' key SQLite hiding).
    7. Else, prompt and pull missing songs from device to local_dir.
    """
    logger.info("[ReverseSync] ======================================================================")
    logger.info("[ReverseSync]                REVERSE SYNCHRONIZER (ADB -> Local)")
    logger.info("[ReverseSync] ======================================================================")
    logger.info(f"[ReverseSync] Destination: {os.path.abspath(local_dir)}")

    os.makedirs(local_dir, exist_ok=True)

    try:
        devices = adb_manager.list_adb_devices()
    except Exception as e:
        logger.error(f"[ReverseSync] Could not list ADB devices: {e}")
        return

    if not devices:
        logger.error("[ReverseSync] No ADB devices connected. Please connect an Android device.")
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
    logger.info(f"[ReverseSync] Source device: {target_device['description']}")
    logger.info("[ReverseSync] ======================================================================")

    # Step 1: Query device songs (cached)
    logger.info(f"[ReverseSync] Querying music library on ADB device [{serial}]...")
    try:
        raw_songs = adb_manager.query_songs_from_device(serial, redis_cfg=redis_cfg, refresh_cache=refresh_cache)
        logger.debug(f"[ReverseSync] Raw ADB output ({len(raw_songs)} chars)")
        device_songs = song_parser.parse_songs(raw_songs)
    except Exception as e:
        logger.error(f"[ReverseSync] Failed to query device songs: {e}")
        return

    logger.info(f"[ReverseSync] Found {len(device_songs)} songs on ADB device.")

    # Step 2: Get local files (cached)
    logger.info(f"[ReverseSync] Scanning local music folder '{local_dir}'...")
    local_files = get_local_music_files(local_dir, audio_extensions, redis_cfg=redis_cfg, refresh_cache=refresh_cache)
    logger.info(f"[ReverseSync] Found {len(local_files)} local audio files.")

    # Step 3: Compare device vs local (with SQLite hide list filtering)
    already_local, missing_locally = compare_device_with_local(device_songs, local_files, show_hidden=show_hidden)

    # Step 4: Check if Interactive Ranger TUI (-i) requested
    if interactive:
        logger.info("[ReverseSync] Launching Ranger-Style Interactive Reverse Sync TUI...")
        res = ranger_reverse_sync_tui.run_ranger_reverse_sync_tui(
            missing_songs=missing_locally,
            local_files=local_files,
            device_serial=serial,
            local_dir=local_dir,
            redis_cfg=redis_cfg
        )
        logger.info(f"[ReverseSync] Session finished. Pulled {len(res['pulled'])} files, hidden {len(res.get('hidden', []))} files.")
        return

    # Step 5: Non-interactive display & CLI execution
    logger.info("[ReverseSync] ----------------------------------------------------------------------")
    logger.info(f"[ReverseSync] Already present locally: {len(already_local)} track(s) (skipped)")
    if already_local:
        for idx, song in enumerate(already_local[:15], 1):
            t = song.get("title") or song.get("_display_name") or "Unknown"
            a = song.get("artist") or "Unknown"
            logger.debug(f"[ReverseSync]   Already local: {t} - {a}")
        if len(already_local) > 15:
            logger.debug(f"[ReverseSync]   ... and {len(already_local) - 15} more already present locally")

    logger.info("[ReverseSync] ----------------------------------------------------------------------")
    logger.info(f"[ReverseSync] Missing locally: {len(missing_locally)} track(s) to pull")
    if not missing_locally:
        logger.info("[ReverseSync] No missing files — all device songs already exist locally.")
        return

    for idx, song in enumerate(missing_locally[:30], 1):
        t = song.get("title") or song.get("_display_name") or "Unknown"
        a = song.get("artist") or "Unknown"
        logger.debug(f"[ReverseSync]   To pull [{idx}]: {t} - {a}")
    if len(missing_locally) > 30:
        logger.debug(f"[ReverseSync]   ... and {len(missing_locally) - 30} more tracks to pull")

    should_pull = auto_confirm
    if not should_pull:
        if os.isatty(0):
            try:
                ans = input(f"Proceed to pull {len(missing_locally)} file(s) from ADB device to '{local_dir}'? [Y/n]: ").strip().lower()
                should_pull = ans in ("", "y", "yes")
            except (KeyboardInterrupt, EOFError):
                should_pull = False
        else:
            logger.info("[ReverseSync] Non-interactive mode: run with --yes or -y to auto-confirm.")
            return

    if not should_pull:
        logger.info("[ReverseSync] Reverse sync cancelled by user.")
        return

    logger.info(f"[ReverseSync] Pulling {len(missing_locally)} file(s) from ADB device to '{local_dir}'...")
    success_count = 0

    for idx, song in enumerate(missing_locally, 1):
        remote_path = song.get("_data")
        display_name = song.get("_display_name") or f"song_{song.get('_id', idx)}.mp3"

        if not remote_path:
            continue

        percent = (idx / len(missing_locally)) * 100
        logger.info(f"[ReverseSync] [{idx}/{len(missing_locally)} {percent:.1f}%] Pulling: {display_name}")

        cmd = ["adb", "-s", serial, "pull", remote_path, os.path.join(local_dir, display_name)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"[ReverseSync] {res.stdout.strip()}")
            success_count += 1
        except subprocess.CalledProcessError as e:
            logger.error(f"[ReverseSync] Failed to pull '{remote_path}': {e.stderr or e.stdout}")

    logger.info("[ReverseSync] ======================================================================")
    logger.info(f"[ReverseSync] Complete: {success_count}/{len(missing_locally)} files pulled successfully.")
