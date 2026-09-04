"""
Music Folder Synchronizer module with high-performance indexing, live progress reporting,
Redis caching, SQLite Hide List database filtering, and Ranger-style Dual-Pane TUI (-i) support.

Scans a local music directory, compares files with songs on an ADB device,
separates already-present songs (skipped by default) from missing songs (to sync),
and uploads missing songs to the specified remote destination (/storage/emulated/0/Music/ADB).
"""
import os
import sys
import re
from typing import List, Dict, Any, Tuple, Optional

import adb_manager
import adb_pusher
import song_parser
import fuzzy_matcher
import ranger_sync_tui
import hide_list_db

DEFAULT_AUDIO_EXTENSIONS = [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"]


def normalize_string(s: str) -> str:
    """Normalize string for fast comparison (lowercase, alphanumeric only)."""
    return re.sub(r"[^a-zA-Z0-9]", "", s.lower())


def scan_local_music_folder(
    folder_path: str,
    extensions: List[str] = None
) -> List[Dict[str, str]]:
    """
    Recursively scan a local directory for audio files matching extensions.
    """
    if not extensions:
        extensions = DEFAULT_AUDIO_EXTENSIONS

    ext_set = set(e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions)
    audio_files = []

    if not os.path.exists(folder_path):
        print(f"[Syncer] Local directory '{folder_path}' does not exist.", file=sys.stderr)
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
    local_files: List[Dict[str, str]],
    serial: str,
    remote_folder: str = "/storage/emulated/0/Music/ADB",
    redis_cfg: Optional[Dict[str, Any]] = None,
    refresh_cache: bool = False,
    show_hidden: bool = False
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    High-performance comparison of local music files with device contents.
    Includes SQLite Hide List filtering, Redis caching, fast lookup, and live progress reporting.
    Returns: (already_present_list, to_sync_list, all_device_songs)
    """
    try:
        raw_songs = adb_manager.query_songs_from_device(serial, redis_cfg=redis_cfg, refresh_cache=refresh_cache)
        device_songs = song_parser.parse_songs(raw_songs)
    except Exception as e:
        print(f"[Syncer] Warning: Failed to query device MediaStore: {e}", file=sys.stderr)
        device_songs = []

    # SQLite Hide List filtering
    if not show_hidden:
        hidden_set = hide_list_db.get_hidden_paths_set()
        local_files = [f for f in local_files if f["path"] not in hidden_set]

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
        norm_name = normalize_string(title_no_ext)
        norm_file = normalize_string(filename)

        if idx % 25 == 0 or idx == total or idx == 1:
            percent = (idx / total) * 100 if total > 0 else 100.0
            sys.stderr.write(f"\r[Syncer] Checking duplicates: {idx}/{total} ({percent:.1f}%) | Processing: {filename[:40]}...")
            sys.stderr.flush()

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
    device_serial: Optional[str] = None,
    remote_dir: str = "/storage/emulated/0/Music/ADB",
    audio_extensions: List[str] = None,
    force_sync: bool = False,
    auto_confirm: bool = False,
    interactive: bool = False,
    redis_cfg: Optional[Dict[str, Any]] = None,
    refresh_cache: bool = False,
    show_hidden: bool = False
):
    """
    Main Sync Folder workflow:
    1. Scan local folder with progress indication.
    2. Filter out SQLite hidden files unless show_hidden=True.
    3. Query target ADB device (using Redis cache if available).
    4. Categorize into (Already Present vs To Sync) with live progress bar.
    5. If interactive (-i), launch Ranger-style Dual-Pane TUI (with 'h' key SQLite hiding).
    6. Else, prompt or auto-upload missing files to remote_dir.
    """
    print(f"\n======================================================================", file=sys.stderr)
    print(f"                     MUSIC FOLDER SYNCHRONIZER                        ", file=sys.stderr)
    print(f"======================================================================", file=sys.stderr)
    print(f" Local Sync Folder : {os.path.abspath(local_dir)}", file=sys.stderr)
    print(f" Remote Destination: {remote_dir}", file=sys.stderr)

    if not os.path.exists(local_dir):
        print(f"\n[ERROR] Local sync directory '{local_dir}' does not exist.", file=sys.stderr)
        return

    try:
        devices = adb_manager.list_adb_devices()
    except Exception as e:
        print(f"\n[ERROR] Could not list ADB devices: {e}", file=sys.stderr)
        return

    if not devices:
        print("\n[ERROR] No ADB devices connected. Please connect an Android device.", file=sys.stderr)
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
    print(f" Target ADB Device : {target_device['description']}", file=sys.stderr)
    print(f"======================================================================\n", file=sys.stderr)

    # Step 1: Scan local files
    print(f"Scanning local music files in '{local_dir}'...", file=sys.stderr)
    local_files = scan_local_music_folder(local_dir, audio_extensions)
    print(f"Found {len(local_files)} local audio files.", file=sys.stderr)

    if not local_files:
        print(f"No audio files found in '{local_dir}'. Nothing to sync.", file=sys.stderr)
        return

    # Step 2: Compare with device (with SQLite hide list filtering)
    print(f"Querying device music library & comparing local files...", file=sys.stderr)
    already_present, to_sync, device_songs = compare_local_files_with_device(
        local_files, serial, remote_dir, redis_cfg=redis_cfg, refresh_cache=refresh_cache, show_hidden=show_hidden
    )

    if force_sync:
        to_sync_final = local_files
    else:
        to_sync_final = to_sync

    # Step 3: Check if Interactive Ranger TUI (-i) requested
    if interactive:
        print("\n[Syncer] Launching Ranger-Style Interactive Sync TUI (-i)...", file=sys.stderr)
        res = ranger_sync_tui.run_ranger_sync_tui(
            to_sync_files=to_sync_final,
            device_songs=device_songs,
            device_serial=serial,
            remote_dir=remote_dir,
            redis_cfg=redis_cfg
        )
        print(f"\n[Syncer] Ranger TUI session finished. Synced {len(res['synced'])} files, Hidden {len(res.get('hidden', []))} files.", file=sys.stderr)
        return

    # Step 4: Non-interactive presentation & CLI sync
    print(f"\n----------------------------------------------------------------------", file=sys.stderr)
    print(f" [SECTION 1] Already Present on Device (Skipped by default - {len(already_present)} files):", file=sys.stderr)
    print(f"----------------------------------------------------------------------", file=sys.stderr)
    if not already_present:
        print("  (None found)", file=sys.stderr)
    else:
        display_limit = 15
        for idx, item in enumerate(already_present[:display_limit], 1):
            loc = item["local"]
            reason = item["match_reason"]
            print(f"  {idx:3d}. {loc['filename']} ({loc['size_formatted']})", file=sys.stderr)
            print(f"       -> {reason}", file=sys.stderr)
        if len(already_present) > display_limit:
            print(f"  ... and {len(already_present) - display_limit} more files already present on device.", file=sys.stderr)

    print(f"\n----------------------------------------------------------------------", file=sys.stderr)
    print(f" [SECTION 2] To Sync / Upload ({len(to_sync_final)} files):", file=sys.stderr)
    print(f"----------------------------------------------------------------------", file=sys.stderr)
    if not to_sync_final:
        print("  (No missing files to sync. All local files are already present on device!)", file=sys.stderr)
        print(f"======================================================================\n", file=sys.stderr)
        return

    display_limit_sync = 30
    for idx, item in enumerate(to_sync_final[:display_limit_sync], 1):
        print(f"  {idx:3d}. {item['rel_path']} ({item['size_formatted']})", file=sys.stderr)
    if len(to_sync_final) > display_limit_sync:
        print(f"  ... and {len(to_sync_final) - display_limit_sync} more files to upload.", file=sys.stderr)

    print(f"======================================================================\n", file=sys.stderr)

    should_sync = auto_confirm
    if not should_sync:
        if sys.stdin.isatty() or os.isatty(0):
            try:
                ans = input(f"Proceed to upload {len(to_sync_final)} file(s) to '{remote_dir}' on ADB device? [Y/n]: ").strip().lower()
                should_sync = ans in ("", "y", "yes")
            except (KeyboardInterrupt, EOFError):
                should_sync = False
        else:
            print("Non-interactive mode: Run with --yes or -y to auto-confirm sync.", file=sys.stderr)
            return

    if not should_sync:
        print("Sync cancelled by user.", file=sys.stderr)
        return

    if not adb_pusher.ensure_remote_folder(serial, remote_dir):
        print("[ERROR] Cannot proceed with sync because remote directory could not be prepared.", file=sys.stderr)
        return

    print(f"\nUploading {len(to_sync_final)} file(s) to ADB device...", file=sys.stderr)
    success_count = 0

    for idx, item in enumerate(to_sync_final, 1):
        percent = (idx / len(to_sync_final)) * 100
        print(f"\n[{idx}/{len(to_sync_final)} - {percent:.1f}%] Syncing: {item['filename']}", file=sys.stderr)
        pushed = adb_pusher.push_song_to_device(serial, item["path"], remote_dir, redis_cfg=redis_cfg)
        if pushed:
            success_count += 1

    print(f"\n======================================================================", file=sys.stderr)
    print(f" Sync Complete: {success_count}/{len(to_sync_final)} files uploaded successfully.", file=sys.stderr)
    print(f"======================================================================\n", file=sys.stderr)
