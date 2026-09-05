#!/usr/bin/env python3
"""
ADB Song Query, FZF Fuzzy Search, Spotify Downloader, Folder Sync, & Reverse Sync Tool

1. Query songs from connected Android devices via ADB content query, or parse existing text file / stdin.
2. Interactive device selection & fzf-like TUI search with lazy matching.
3. Download songs from Spotify links or search queries directly into songs/download/ directory.
4. Synchronize local music folders (e.g. /home/aruncs/Music) with ADB device.
5. Reverse Sync (ADB Device -> Local Folder /home/aruncs/Music) with Ranger Dual-Pane TUI.
6. Interactive Ranger-style Dual-Pane TUI sync (-i) with SQLite Hide List ('h' key).
7. Persistent SQLite database (sync_hide_list.db) for hiding cumbersome files across runs.
8. Main Interactive Navigation Menu TUI when launched with no arguments.
9. Configurable via config.json with strict Redis caching (localhost:8998, pass: greenIsBest).
"""
import sys
import os
import argparse
import json
from typing import List, Dict, Any

import song_parser
import fuzzy_matcher
import adb_manager
import fzf_tui
import config_manager
import syncer
import reverse_syncer
import redis_cache
import hide_list_db
import main_menu_tui
import over_ip.workflow as over_ip_workflow
import over_ip.server as over_ip_server
from downloader import DownloadManager


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query, fuzzy search, download, sync, reverse-sync, and Over-IP sync songs with ADB devices and peers.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  1. Over-IP Sync across devices over HTTP:
     python app.py --ip

  2. Launch Over-IP Flask REST API server:
     python app.py --serve-ip

  3. Interactive Ranger-style Dual-Pane Reverse Sync (ADB Device -> Local Folder):
     python app.py --reverse-sync -i

  4. Interactive Ranger-style Dual-Pane Sync (Local Folder -> ADB Device):
     python app.py --sync -i

  5. List all files currently hidden in SQLite database:
     python app.py --list-hidden

  6. Unhide a file (or 'all') from SQLite database:
     python app.py --unhide all

  7. Include hidden files during sync:
     python app.py --sync --show-hidden

  6. Launch Interactive Main Menu:
     python app.py
"""
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom config.json file."
    )
    parser.add_argument(
        "--ip",
        nargs="?",
        const="",
        type=str,
        help="Sync music across devices over HTTP IP address (e.g. --ip 192.168.1.50)."
    )
    parser.add_argument(
        "--serve-ip",
        action="store_true",
        help="Start Flask REST API server to serve local music library over HTTP."
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Synchronize local music folder with ADB device."
    )
    parser.add_argument(
        "--reverse-sync",
        action="store_true",
        help="Reverse sync: Pull missing songs from ADB device into local music folder."
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Launch Ranger-style interactive dual-pane TUI during folder sync or reverse sync."
    )
    parser.add_argument(
        "--show-hidden",
        action="store_true",
        help="Include files hidden in SQLite database during sync operations."
    )
    parser.add_argument(
        "--list-hidden",
        action="store_true",
        help="List all files stored in the SQLite hide list database (sync_hide_list.db) and exit."
    )
    parser.add_argument(
        "--list-synced",
        action="store_true",
        help="List all files recorded in the SQLite synced history database (sync_hide_list.db) and exit."
    )
    parser.add_argument(
        "--unhide",
        type=str,
        help="Remove specified file path (or 'all') from the SQLite hide list database and exit."
    )
    parser.add_argument(
        "--sync-folder",
        type=str,
        help="Local music folder to sync (overrides config.json local_sync_folder)."
    )
    parser.add_argument(
        "--remote-dir",
        type=str,
        help="Target folder on ADB device (overrides config.json remote_adb_folder)."
    )
    parser.add_argument(
        "--force-sync",
        action="store_true",
        help="Include songs already present on device in sync upload list."
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Automatically confirm sync, reverse-sync, and push operations without prompting."
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Bypass Redis cache and re-query live ADB device."
    )
    parser.add_argument(
        "-dl", "--download",
        type=str,
        help="Spotify track/album URL or song query to download into songs/download/ directory."
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        help="Target folder for downloaded songs (overrides config.json download_folder)."
    )
    parser.add_argument(
        "--use-telegram",
        action="store_true",
        help="Force using Telegram Deezload bot for Spotify link downloading."
    )
    parser.add_argument(
        "--push-adb",
        action="store_true",
        default=None,
        help="Automatically push downloaded song to ADB device."
    )
    parser.add_argument(
        "--no-push-adb",
        action="store_false",
        dest="push_adb",
        help="Skip pushing downloaded song to ADB device."
    )
    parser.add_argument(
        "-d", "--device",
        type=str,
        help="ADB device serial number (or index)."
    )
    parser.add_argument(
        "-s", "--search",
        type=str,
        help="Non-interactive search query (lazy fuzzy match)."
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Path to file containing ADB content query data (e.g., songs.txt)."
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "path", "csv"],
        default="text",
        help="Output format (default: text)."
    )
    parser.add_argument(
        "-l", "--list-devices",
        action="store_true",
        help="List connected ADB devices and exit."
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=None,
        help="Limit number of search results printed in non-interactive mode."
    )

    return parser.parse_args()


def output_songs(songs: List[Dict[str, Any]], fmt: str):
    """Output songs in specified format (text, json, path, csv)."""
    if not songs:
        return

    if fmt == "json":
        clean_songs = []
        for s in songs:
            s_copy = dict(s)
            s_copy.pop("searchable_text", None)
            clean_songs.append(s_copy)
        print(json.dumps(clean_songs, indent=2))
    elif fmt == "path":
        for s in songs:
            path = s.get("_data")
            if path:
                print(path)
    elif fmt == "csv":
        import csv
        writer = csv.writer(sys.stdout)
        writer.writerow(["id", "title", "artist", "album", "duration", "size", "data_path"])
        for s in songs:
            writer.writerow([
                s.get("_id", ""),
                s.get("title", ""),
                s.get("artist", ""),
                s.get("album", ""),
                s.get("duration_formatted", ""),
                s.get("size_formatted", ""),
                s.get("_data", "")
            ])
    else: # text format
        for idx, s in enumerate(songs, 1):
            title = s.get("title") or "Unknown"
            artist = s.get("artist") or "Unknown"
            album = s.get("album") or "Unknown"
            dur = s.get("duration_formatted") or "00:00"
            path = s.get("_data") or ""
            print(f"{idx:4d}. {title} - {artist} [{album}] ({dur})")
            if path:
                print(f"      Path: {path}")


def main():
    args = parse_args()

    # Handle SQLite Hide List management CLI flags
    if args.list_hidden:
        records = hide_list_db.get_all_hidden_records()
        if not records:
            print("No hidden files in SQLite database (sync_hide_list.db).")
        else:
            print(f"Hidden Files in SQLite Database ({len(records)} entries):")
            for r in records:
                print(f"  [{r['id']}] {r['filename']} | Path: {r['filepath']} (Hidden at: {r['hidden_at']})")
        return

    if args.unhide:
        if args.unhide.lower() == "all":
            hide_list_db.clear_all_hidden()
        else:
            hide_list_db.remove_hidden_file(args.unhide)
        return

    # Load settings from config.json
    cfg = config_manager.load_config(args.config)

    # Merge configuration defaults with CLI overrides
    target_device_serial = args.device or cfg.get("default_device_serial")
    local_sync_dir = args.sync_folder or cfg.get("local_sync_folder", "/home/aruncs/Music")
    remote_adb_dir = args.remote_dir or cfg.get("remote_adb_folder", "/storage/emulated/0/Music/ADB")
    download_dir = args.download_dir or cfg.get("download_folder", "songs/download")
    use_telegram = args.use_telegram or cfg.get("use_telegram", False)
    push_adb_setting = args.push_adb if args.push_adb is not None else cfg.get("auto_push_adb", None)
    audio_extensions = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus"])
    redis_cfg = cfg.get("redis")

    if args.list_synced:
        records = hide_list_db.get_all_synced_records(device_serial=target_device_serial)
        if not records:
            dev_str = f" for device [{target_device_serial}]" if target_device_serial else ""
            print(f"No synced track history found{dev_str} in SQLite database (sync_hide_list.db).")
        else:
            header = f"Synced Tracks History{f' for [{target_device_serial}]' if target_device_serial else ''} ({len(records)} entries):"
            print(header)
            for r in records:
                print(f"  [{r['id']}] {r['filename']} | Device: {r['device_serial']} | Remote: {r['remote_dir']} (Synced: {r['synced_at']})")
        return

    # Handle --serve-ip Flask API Server
    if args.serve_ip:
        over_ip_server.start_server(host="0.0.0.0", port=5000)
        sys.exit(0)

    # Handle --ip Over-IP HTTP Synchronization Workflow
    if args.ip is not None:
        over_ip_workflow.run_over_ip_workflow(
            target_ip=args.ip if args.ip else None,
            interactive=True,
            config_path=args.config,
            redis_cfg=redis_cfg,
            refresh_cache=args.refresh_cache,
            show_hidden=args.show_hidden
        )
        sys.exit(0)

    # If no flags passed in terminal TTY mode, show Interactive Main Menu
    if len(sys.argv) == 1 and (sys.stdin.isatty() or os.isatty(0)):
        choice = main_menu_tui.show_main_menu_tui()
        if not choice:
            print("Exiting.", file=sys.stderr)
            sys.exit(0)

        if choice == "search":
            pass
        elif choice == "sync":
            args.sync = True
            if sys.stdin.isatty() or os.isatty(0):
                try:
                    ans = input("\nLaunch Ranger-Style Interactive Dual-Pane TUI (-i)? [Y/n]: ").strip().lower()
                    if ans in ("", "y", "yes"):
                        args.interactive = True
                except (KeyboardInterrupt, EOFError):
                    pass
        elif choice == "download":
            try:
                query_link = input("\nEnter Spotify link or song query to download: ").strip()
                if query_link:
                    args.download = query_link
            except (KeyboardInterrupt, EOFError):
                sys.exit(0)
        elif choice == "cache_refresh":
            args.refresh_cache = True
            print("\nRefreshing Redis cache...", file=sys.stderr)
        elif choice == "reverse_sync":
            args.reverse_sync = True
            if sys.stdin.isatty() or os.isatty(0):
                try:
                    ans = input("\nLaunch Ranger-Style Interactive Reverse Sync TUI (-i)? [Y/n]: ").strip().lower()
                    if ans in ("", "y", "yes"):
                        args.interactive = True
                except (KeyboardInterrupt, EOFError):
                    pass
        elif choice == "over_ip":
            args.ip = ""
            over_ip_workflow.run_over_ip_workflow(
                target_ip=None,
                interactive=True,
                config_path=args.config,
                redis_cfg=redis_cfg,
                refresh_cache=args.refresh_cache,
                show_hidden=args.show_hidden
            )
            sys.exit(0)

    # Handle --reverse-sync mode
    if args.reverse_sync:
        reverse_syncer.run_reverse_sync_workflow(
            local_dir=local_sync_dir,
            device_serial=target_device_serial,
            audio_extensions=audio_extensions,
            auto_confirm=args.yes,
            interactive=args.interactive,
            redis_cfg=redis_cfg,
            refresh_cache=args.refresh_cache,
            show_hidden=args.show_hidden
        )
        sys.exit(0)

    # Handle --sync mode
    if args.sync or args.interactive:
        syncer.run_sync_workflow(
            local_dir=local_sync_dir,
            device_serial=target_device_serial,
            remote_dir=remote_adb_dir,
            audio_extensions=audio_extensions,
            force_sync=args.force_sync,
            auto_confirm=args.yes,
            interactive=args.interactive,
            redis_cfg=redis_cfg,
            refresh_cache=args.refresh_cache,
            show_hidden=args.show_hidden
        )
        sys.exit(0)

    # Handle --download (-dl)
    if args.download:
        mgr = DownloadManager(
            output_dir=download_dir,
            use_telegram=use_telegram,
            device_serial=target_device_serial,
            auto_push_adb=push_adb_setting
        )
        downloaded_file = mgr.download(args.download)
        if downloaded_file:
            sys.exit(0)
        else:
            sys.exit(1)

    # Handle --list-devices
    if args.list_devices:
        try:
            devices = adb_manager.list_adb_devices()
            if not devices:
                print("No connected ADB devices found.")
            else:
                print(f"Connected ADB devices ({len(devices)}):")
                for idx, dev in enumerate(devices, 1):
                    print(f"  [{idx}] {dev['serial']} | Model: {dev['model']} | State: {dev['state']}")
        except Exception as e:
            print(f"Error listing devices: {e}", file=sys.stderr)
            sys.exit(1)
        return

    songs = []
    source_name = "Unknown Source"

    # Step 1: Determine source of song data (File, Stdin Pipe, or ADB Device)
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        songs = song_parser.parse_songs(content)
        source_name = f"File: {os.path.basename(args.file)}"

    elif not sys.stdin.isatty():
        content = sys.stdin.read()
        songs = song_parser.parse_songs(content)
        source_name = "Piped Stdin"

    else:
        try:
            devices = adb_manager.list_adb_devices()
        except Exception as e:
            print(f"Error checking ADB devices: {e}", file=sys.stderr)
            sys.exit(1)

        if not devices:
            print("Error: No ADB devices connected. Please connect an Android device via USB/Wi-Fi.", file=sys.stderr)
            sys.exit(1)

        target_device = None

        if target_device_serial:
            for dev in devices:
                if dev["serial"] == target_device_serial or dev["model"] == target_device_serial:
                    target_device = dev
                    break
            if not target_device:
                try:
                    idx = int(target_device_serial)
                    if 1 <= idx <= len(devices):
                        target_device = devices[idx - 1]
                except ValueError:
                    pass

            if not target_device:
                target_device = {"serial": target_device_serial, "model": target_device_serial, "description": target_device_serial}
        else:
            target_device = adb_manager.select_device_from_stdin(devices)
            if not target_device:
                if len(devices) == 1:
                    target_device = devices[0]
                else:
                    target_device = fzf_tui.select_device_tui(devices)

        if not target_device:
            print("No device selected. Exiting.", file=sys.stderr)
            sys.exit(1)

        print(f"Querying songs from ADB device {target_device['description']}...", file=sys.stderr)
        try:
            raw_output = adb_manager.query_songs_from_device(
                target_device["serial"], redis_cfg=redis_cfg, refresh_cache=args.refresh_cache
            )
            songs = song_parser.parse_songs(raw_output)
            source_name = f"ADB: {target_device['serial']}"
        except Exception as e:
            print(f"Failed to query songs from device: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Loaded {len(songs)} songs from {source_name}.", file=sys.stderr)

    if not songs:
        print("No music files found in specified source.", file=sys.stderr)
        sys.exit(0)

    # Step 2: Search or Interactive Selection
    if args.search is not None:
        results = fuzzy_matcher.filter_and_rank_songs(args.search, songs)
        if args.limit and args.limit > 0:
            results = results[:args.limit]
        output_songs(results, args.format)
    else:
        selected = fzf_tui.search_songs_tui(songs, device_info=source_name)
        if selected:
            output_songs([selected], args.format)
        else:
            print("No song selected.", file=sys.stderr)


if __name__ == "__main__":
    main()
