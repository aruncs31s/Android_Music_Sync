"""
ADB device connection & MediaStore content provider manager.
Handles discovering ADB devices, selecting devices interactively or via stdin/args,
and querying songs from device media content provider with optional Redis caching.
"""
import sys
import subprocess
import shutil
from typing import List, Dict, Any, Optional
import database.redis_cache as redis_cache

MEDIA_URI = "content://media/external/audio/media"
MEDIA_PROJECTION = "_id:_display_name:title:artist:album:album_artist:composer:track:year:duration:mime_type:_size:_data:date_added:date_modified"
MEDIA_WHERE = "is_music=1"

def is_adb_available() -> bool:
    """Check if adb binary is available in PATH."""
    return shutil.which("adb") is not None

def list_adb_devices() -> List[Dict[str, str]]:
    """
    Query attached ADB devices using 'adb devices -l'.
    Returns a list of device dicts containing serial, state, model, product.
    """
    if not is_adb_available():
        raise RuntimeError("ADB binary not found. Please install Android Platform Tools (adb).")

    try:
        res = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to run 'adb devices': {e.stderr}")

    devices = []
    lines = res.stdout.strip().splitlines()
    for line in lines[1:]: # Skip 'List of devices attached' header
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        serial = parts[0]
        state = parts[1]

        extra_info = {}
        for token in parts[2:]:
            if ":" in token:
                k, v = token.split(":", 1)
                extra_info[k] = v

        model = extra_info.get("model") or extra_info.get("device") or "Android Device"
        product = extra_info.get("product") or ""

        devices.append({
            "serial": serial,
            "state": state,
            "model": model,
            "product": product,
            "description": f"{serial} ({model})" if model else serial
        })

    return devices

def select_device_from_stdin(devices: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Try to read device selection from stdin non-interactively (e.g. index or serial).
    """
    if sys.stdin.isatty():
        return None

    line = sys.stdin.readline().strip()
    if not line:
        return None

    for dev in devices:
        if dev["serial"] == line:
            return dev

    try:
        idx = int(line)
        if 1 <= idx <= len(devices):
            return devices[idx - 1]
        elif 0 <= idx < len(devices):
            return devices[idx]
    except ValueError:
        pass

    return None

def query_songs_from_device(
    serial: str,
    redis_cfg: Optional[Dict[str, Any]] = None,
    refresh_cache: bool = False
) -> str:
    """
    Execute 'adb shell content query ...' on target device serial.
    Checks Redis cache first if redis_cfg is provided and refresh_cache is False.
    """
    # 1. Check Redis cache if enabled and not refreshing
    if not refresh_cache and redis_cfg:
        cached_output = redis_cache.get_cached_songs(serial, redis_cfg)
        if cached_output:
            return cached_output

    # 2. Query live ADB device
    cmd = [
        "adb", "-s", serial, "shell", "content", "query",
        "--uri", MEDIA_URI,
        "--where", MEDIA_WHERE,
        "--projection", MEDIA_PROJECTION
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = res.stdout

        # 3. Store result in Redis cache if enabled
        if redis_cfg:
            redis_cache.set_cached_songs(serial, output, redis_cfg)

        return output
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error querying songs from device {serial}: {e.stderr or e.stdout}")


def delete_song_from_device(
    serial: str,
    filepath: str,
    song_id: Optional[str] = None,
    redis_cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Permanently delete an audio file from an Android ADB device.
    1. Removes the physical file using 'adb -s <serial> shell rm -f <quoted_path>'
    2. Deletes the MediaStore record via 'adb -s <serial> shell content delete ...'
    3. Triggers media scanner broadcast to refresh Android's media indexing.
    4. Invalidates Redis cache for this device.
    """
    import os
    import shlex

    if not is_adb_available():
        raise RuntimeError("ADB binary not found. Please install Android Platform Tools.")

    if not filepath or not filepath.strip():
        raise ValueError("Filepath cannot be empty.")

    clean_path = filepath.strip()
    quoted_path = shlex.quote(clean_path)

    # 1. Delete physical file via adb shell rm -f
    cmd_rm = ["adb", "-s", serial, "shell", f"rm -f {quoted_path}"]
    try:
        subprocess.run(cmd_rm, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ADB rm error on device {serial}: {e.stderr or e.stdout}")

    # 2. Delete from Android MediaStore database
    try:
        if song_id and str(song_id).isdigit():
            cmd_content = [
                "adb", "-s", serial, "shell", "content", "delete",
                "--uri", MEDIA_URI,
                "--where", f"_id={song_id}"
            ]
            subprocess.run(cmd_content, capture_output=True, text=True)

        # Also attempt cleanup by _data
        cmd_content_path = [
            "adb", "-s", serial, "shell", "content", "delete",
            "--uri", MEDIA_URI,
            "--where", f"_data={quoted_path}"
        ]
        subprocess.run(cmd_content_path, capture_output=True, text=True)
    except Exception:
        pass

    # 3. Notify Android MediaScanner about the removal
    try:
        cmd_scan = [
            "adb", "-s", serial, "shell",
            f"am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{clean_path}"
        ]
        subprocess.run(cmd_scan, capture_output=True, text=True)
    except Exception:
        pass

    # 4. Invalidate Redis cache
    if redis_cfg:
        redis_cache.invalidate_cache(serial, redis_cfg)
        redis_cache.delete_cache(redis_cfg, f"cache:device_songs:adb_{serial}")
        redis_cache.delete_cache(redis_cfg, f"cache:device_songs:adb:{serial}")
        redis_cache.delete_cache(redis_cfg, "cache:devices:summary")
        redis_cache.delete_cache(redis_cfg, "cache:dashboard:stats")

    return {
        "status": "success",
        "message": f"Successfully deleted '{os.path.basename(clean_path)}' from ADB device [{serial}]."
    }

