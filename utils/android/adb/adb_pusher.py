"""
ADB File Pusher & Duplicate Detection Module.

Handles checking for duplicate songs on ADB device, verifying/creating remote directory
(/storage/emulated/0/Music/ADB), prompting the user, pushing files, recording synced tracks in SQLite DB,
and triggering media scanner refresh broadcasts.
"""
import sys
import os
import subprocess
from typing import Optional, Dict, Any, List

import utils.android.adb.adb_manager as adb_manager
import song_parser
import fuzzy_matcher
import redis_cache
import hide_list_db
from utils import get_logger
logger = get_logger()

TARGET_REMOTE_DIR = "/storage/emulated/0/Music/ADB"


def check_remote_folder_exists(serial: str, remote_dir: str = TARGET_REMOTE_DIR) -> bool:
    """Check if directory exists on the ADB device."""
    cmd = ["adb", "-s", serial, "shell", f"test -d '{remote_dir}' && echo 1 || echo 0"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip() == "1"
    except subprocess.CalledProcessError:
        return False


def ensure_remote_folder(serial: str, remote_dir: str = TARGET_REMOTE_DIR) -> bool:
    """
    Verify if remote directory exists on ADB device.
    If not, attempt to create it.
    If creation fails, prompt the user to manually create it.
    """
    if check_remote_folder_exists(serial, remote_dir):
        return True

    logger.info(f"[ADB Pusher] Folder '{remote_dir}' does not exist on device {serial}. Attempting to create...")

    cmd = ["adb", "-s", serial, "shell", f"mkdir -p '{remote_dir}'"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"[ADB Pusher] Failed to create directory '{remote_dir}' on device: {e.stderr}")

    if check_remote_folder_exists(serial, remote_dir):
        logger.info(f"[ADB Pusher] Successfully created folder '{remote_dir}' on device.")
        return True

    logger.error(f"[ADB Pusher] Unable to create folder '{remote_dir}' on device automatically.")
    logger.error(f"[ADB Pusher] ACTION REQUIRED: Please manually create '{remote_dir}' on your Android device and try again.")
    return False


def refresh_device_media_scanner(serial: str, remote_path: str) -> bool:
    """
    Trigger Android MediaScanner broadcast scan for file or directory path.
    Example: file:///storage/emulated/0/Music/ADB
    """
    if not remote_path.startswith("file://"):
        file_uri = f"file://{remote_path}"
    else:
        file_uri = remote_path

    cmd = [
        "adb", "-s", serial, "shell", "am", "broadcast",
        "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d", file_uri
    ]
    try:
        logger.info(f"[MediaScanner] Refreshing media library on device [{serial}] for '{file_uri}'...")
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = res.stdout.strip()
        if output:
            logger.debug(f"[MediaScanner] {output}")
        return True
    except Exception as e:
        logger.warning(f"[MediaScanner] Broadcast warning: {e}")
        return False


def find_duplicate_song(
    serial: str,
    local_filepath: str,
    redis_cfg: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Check if a matching song already exists on the target ADB device.
    Checks SQLite synced_files history, MediaStore content query, and remote folder files.
    Returns details of duplicate song if found, else None.
    """
    filename = os.path.basename(local_filepath)
    filename_no_ext = os.path.splitext(filename)[0]

    # Check SQLite synced_files history for this device serial
    synced_set = hide_list_db.get_synced_paths_set(serial)
    if local_filepath in synced_set:
        return {
            "title": filename_no_ext,
            "_display_name": filename,
            "_data": f"Recorded in SQLite synced_files database for [{serial}]"
        }

    try:
        raw_songs = adb_manager.query_songs_from_device(serial, redis_cfg=redis_cfg)
        existing_songs = song_parser.parse_songs(raw_songs)
    except Exception:
        existing_songs = []

    matches = fuzzy_matcher.filter_and_rank_songs(filename_no_ext, existing_songs)
    if matches:
        top_match = matches[0]
        match_title = top_match.get("title") or ""
        match_display = top_match.get("_display_name") or ""
        if filename_no_ext.lower() in match_title.lower() or filename_no_ext.lower() in match_display.lower():
            return top_match

    cmd = ["adb", "-s", serial, "shell", f"test -f '{TARGET_REMOTE_DIR}/{filename}' && echo 1 || echo 0"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if res.stdout.strip() == "1":
            return {
                "title": filename_no_ext,
                "_display_name": filename,
                "_data": f"{TARGET_REMOTE_DIR}/{filename}"
            }
    except Exception:
        pass

    return None


def push_song_to_device(
    serial: str,
    local_filepath: str,
    remote_dir: str = TARGET_REMOTE_DIR,
    redis_cfg: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Push a local audio file to target ADB directory, record in SQLite DB, trigger media scan, and evict Redis cache.
    """
    if not os.path.exists(local_filepath):
        logger.error(f"[ADB Pusher] Local file '{local_filepath}' not found.")
        return False

    if not ensure_remote_folder(serial, remote_dir):
        return False

    filename = os.path.basename(local_filepath)
    remote_path = f"{remote_dir}/{filename}"

    logger.info(f"[ADB Pusher] Pushing '{filename}' to device [{serial}] '{remote_dir}/'...")

    cmd = ["adb", "-s", serial, "push", local_filepath, f"{remote_dir}/"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(f"[ADB Pusher] {res.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"[ADB Pusher] ADB push failed: {e.stderr or e.stdout}")
        return False

    # Record pushed track in SQLite synced_files table for this device serial
    hide_list_db.add_synced_file(local_filepath, filename, serial, remote_dir)

    # Trigger Android Media Scanner broadcast for pushed file
    refresh_device_media_scanner(serial, remote_path)

    # Evict cached Redis song list so next query fetches fresh MediaStore state
    if redis_cfg:
        redis_cache.invalidate_cache(serial, redis_cfg)

    logger.info(f"[ADB Pusher] Successfully pushed to device: {remote_path}")
    return True


def handle_post_download_adb_workflow(
    local_filepath: str,
    device_serial: Optional[str] = None,
    auto_confirm: Optional[bool] = None,
    redis_cfg: Optional[Dict[str, Any]] = None
):
    """
    Main post-download workflow:
    1. Check attached ADB devices.
    2. Check for duplicate song match on device & notify user.
    3. Ask user 'push it to adb?'.
    4. Check/create remote folder '/storage/emulated/0/Music/ADB'.
    5. Push file to device, record in SQLite, refresh media scanner, and clear cache.
    """
    try:
        devices = adb_manager.list_adb_devices()
    except Exception:
        devices = []

    if not devices:
        logger.info("[ADB Pusher] No ADB devices connected. File saved locally.")
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
    logger.info(f"[ADB Pusher] Checking device: {target_device['description']}")

    duplicate = find_duplicate_song(serial, local_filepath, redis_cfg=redis_cfg)
    if duplicate:
        logger.info(f"[ADB Pusher] Duplicate found on device: title='{duplicate.get('title', 'Unknown')}', path='{duplicate.get('_data', 'Unknown')}', downloaded='{os.path.basename(local_filepath)}'")

    should_push = False
    if auto_confirm is True:
        should_push = True
    elif auto_confirm is False:
        should_push = False
    else:
        if sys.stdin.isatty() or os.isatty(0):
            try:
                response = input("Push it to ADB device? [y/N]: ").strip().lower()
                should_push = response in ("y", "yes")
            except (KeyboardInterrupt, EOFError):
                should_push = False
        else:
            logger.info("[ADB Pusher] Run with --push-adb to automatically push downloaded songs to your ADB device.")

    if should_push:
        push_song_to_device(serial, local_filepath, redis_cfg=redis_cfg)
        refresh_device_media_scanner(serial, TARGET_REMOTE_DIR)
    else:
        logger.info("[ADB Pusher] Skipped pushing to ADB device.")
