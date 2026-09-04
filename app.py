#!/usr/bin/env python3
"""
ADB Song Query, FZF Fuzzy Search, Spotify Downloader, & Folder Sync Tool

1. Query songs from connected Android devices via ADB content query, or parse existing text file / stdin.
2. Interactive device selection & fzf-like TUI search with lazy matching.
3. Download songs from Spotify links or search queries directly into songs/download/ directory.
4. Synchronize local music folders (e.g. /home/aruncs/Music) with ADB device.
5. Interactive Ranger-style Dual-Pane TUI sync (-i).
6. All settings configurable via config.json with Redis caching (host: localhost, port: 8998, pass: greenIsBest).
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
import redis_cache
from downloader import DownloadManager


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query, fuzzy search, download, and sync songs with ADB devices.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  1. Interactive Ranger-style Dual-Pane TUI sync:
     python app.py --sync -i

  2. Synchronize local music folder (/home/aruncs/Music) with connected ADB device:
     python app.py --sync

  3. Download song from Spotify link & push to ADB device:
     python app.py -dl "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT" --push-adb

  4. Download song by query to songs/download/:
     python app.py -dl "Arijit Singh Kesariya"

  5. Interactive device selection & FZF song search:
     python app.py
"""
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom config.json file."
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Synchronize local music folder with ADB device."
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Launch Ranger-style interactive dual-pane TUI during folder sync."
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
        help="Automatically confirm sync and push operations without prompting."
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
            refresh_cache=args.refresh_cache
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
