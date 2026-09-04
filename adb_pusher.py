"""
ADB File Pusher & Duplicate Detection Module.

Handles checking for duplicate songs on ADB device, verifying/creating remote directory
(/storage/emulated/0/Music/ADB), prompting the user, pushing files, and triggering media scan.
"""
import sys
import os
import subprocess
from typing import Optional, Dict, Any, List

import adb_manager
import song_parser
import fuzzy_matcher
import redis_cache

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

    print(f"\n[ADB Pusher] Folder '{remote_dir}' does not exist on device {serial}. Attempting to create...", file=sys.stderr)

    cmd = ["adb", "-s", serial, "shell", f"mkdir -p '{remote_dir}'"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ADB Pusher] Failed to create directory '{remote_dir}' on device: {e.stderr}", file=sys.stderr)

    if check_remote_folder_exists(serial, remote_dir):
        print(f"[ADB Pusher] Successfully created folder '{remote_dir}' on device.", file=sys.stderr)
        return True

    print(f"\n[ERROR] Unable to create folder '{remote_dir}' on device automatically.", file=sys.stderr)
    print(f"[ACTION REQUIRED] Please manually create the folder '{remote_dir}' on your Android device and try again.\n", file=sys.stderr)
    return False


def find_duplicate_song(
    serial: str,
    local_filepath: str,
    redis_cfg: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Check if a matching song already exists on the target ADB device.
    Checks MediaStore content query and existing files in remote target directory.
    Returns details of duplicate song if found, else None.
    """
    filename = os.path.basename(local_filepath)
    filename_no_ext = os.path.splitext(filename)[0]

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
    Push a local audio file to target ADB directory, trigger media scan, and evict Redis cache.
    """
    if not os.path.exists(local_filepath):
        print(f"[ADB Pusher] Local file '{local_filepath}' not found.", file=sys.stderr)
        return False

    if not ensure_remote_folder(serial, remote_dir):
        return False

    filename = os.path.basename(local_filepath)
    remote_path = f"{remote_dir}/{filename}"

    print(f"[ADB Pusher] Pushing '{filename}' to device [{serial}] '{remote_dir}/'...", file=sys.stderr)

    cmd = ["adb", "-s", serial, "push", local_filepath, f"{remote_dir}/"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(res.stdout.strip(), file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[ADB Pusher] ADB push failed: {e.stderr or e.stdout}", file=sys.stderr)
        return False

    # Trigger Android Media Scanner broadcast
    print(f"[ADB Pusher] Triggering media scanner for '{remote_path}'...", file=sys.stderr)
    scan_cmd = [
        "adb", "-s", serial, "shell", "am", "broadcast",
        "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d", f"file://{remote_path}"
    ]
    try:
        subprocess.run(scan_cmd, capture_output=True, text=True, check=False)
    except Exception:
        pass

    # Evict cached Redis song list so next query fetches fresh MediaStore state
    if redis_cfg:
        redis_cache.invalidate_cache(serial, redis_cfg)

    print(f"[ADB Pusher] Successfully pushed to device: {remote_path}", file=sys.stderr)
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
    5. Push file to device and clear cache.
    """
    try:
        devices = adb_manager.list_adb_devices()
    except Exception:
        devices = []

    if not devices:
        print("\n[ADB Pusher] No ADB devices connected. File saved locally.", file=sys.stderr)
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
    print(f"\n==================================================", file=sys.stderr)
    print(f"[ADB Pusher] Checking device: {target_device['description']}", file=sys.stderr)

    duplicate = find_duplicate_song(serial, local_filepath, redis_cfg=redis_cfg)
    if duplicate:
        print(f"\n[NOTICE] A matching song was found on your device!", file=sys.stderr)
        print(f"         Existing Title : {duplicate.get('title', 'Unknown')}", file=sys.stderr)
        print(f"         Existing Path  : {duplicate.get('_data', 'Unknown')}", file=sys.stderr)
        print(f"         Downloaded File: {os.path.basename(local_filepath)}\n", file=sys.stderr)

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
            print("Run with --push-adb to automatically push downloaded songs to your ADB device.", file=sys.stderr)

    if should_push:
        push_song_to_device(serial, local_filepath, redis_cfg=redis_cfg)
    else:
        print("[ADB Pusher] Skipped pushing to ADB device.", file=sys.stderr)
