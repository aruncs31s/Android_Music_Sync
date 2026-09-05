"""
Dashboard Statistics, Device Scanner, & Duplicate Detection Manager for Web UI.
Calculates metric counts:
1. Total Song Counts in each device (Local folders, ADB devices, Over-IP peers)
2. Synced Counts (from ui/db.db synced_files table)
3. Hidden Songs Count (from ui/db.db hidden_files table)
4. Duplicates Count (clusters of matching titles/artists/filenames)
"""
import os
import sys
from collections import defaultdict
from typing import List, Dict, Any

import config_manager
import audio_metadata
import over_ip.song_scanner as song_scanner
import over_ip.client as ip_client
import adb_manager
import ui.db_manager as ui_db
import song_parser
from utils import get_logger

logger = get_logger()


def detect_duplicate_songs(songs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect duplicate audio files across local music folders.
    Groups songs by title + artist or normalized filename.
    Returns dictionary with total duplicate count and duplicate clusters.
    """
    by_key = defaultdict(list)
    by_filename = defaultdict(list)

    for s in songs:
        title = (s.get("title") or "").strip().lower()
        artist = (s.get("artist") or "").strip().lower()
        filename = (s.get("filename") or os.path.basename(s.get("filepath", ""))).strip().lower()

        if title and title != "unknown":
            key = f"{artist} - {title}" if artist and artist != "unknown" else title
            by_key[key].append(s)

        if filename:
            by_filename[filename].append(s)

    clusters = []
    seen_paths = set()

    for key, song_group in by_key.items():
        if len(song_group) > 1:
            cluster_paths = set(s.get("filepath") for s in song_group if s.get("filepath"))
            if len(cluster_paths) > 1:
                clusters.append({
                    "cluster_name": key.title(),
                    "match_type": "title_artist",
                    "count": len(song_group),
                    "songs": song_group
                })
                seen_paths.update(cluster_paths)

    for fn, song_group in by_filename.items():
        if len(song_group) > 1:
            cluster_paths = set(s.get("filepath") for s in song_group if s.get("filepath"))
            if len(cluster_paths) > 1 and not cluster_paths.issubset(seen_paths):
                clusters.append({
                    "cluster_name": fn,
                    "match_type": "filename",
                    "count": len(song_group),
                    "songs": song_group
                })
                seen_paths.update(cluster_paths)

    total_duplicate_files = sum(len(c["songs"]) - 1 for c in clusters)
    logger.info(f"Duplicate scan finished: Found {len(clusters)} clusters ({total_duplicate_files} duplicate files).")

    return {
        "total_duplicates": total_duplicate_files,
        "cluster_count": len(clusters),
        "clusters": clusters
    }


def scan_adb_devices_info() -> List[Dict[str, Any]]:
    """
    Perform a live scan of connected ADB devices and query song counts.
    """
    cfg = config_manager.load_config()
    redis_cfg = cfg.get("redis")
    adb_list = []
    logger.info("Performing live ADB device discovery scan...")

    try:
        adb_devs = adb_manager.list_adb_devices()
        logger.info(f"ADB discovery found {len(adb_devs)} connected ADB device(s).")
        for dev in adb_devs:
            serial = dev["serial"]
            model = dev.get("model") or serial
            cnt = 0
            try:
                raw_out = adb_manager.query_songs_from_device(serial, redis_cfg=redis_cfg)
                parsed = song_parser.parse_songs(raw_out)
                cnt = len(parsed)
                logger.info(f"Queried ADB device [{serial}] ({model}): {cnt} songs.")
            except Exception as err:
                logger.error(f"Error querying songs from ADB device [{serial}]: {err}")
                pass
            except Exception:
                pass

            adb_list.append({
                "id": f"adb_{serial}",
                "name": f"Android ADB: {model}",
                "type": "ADB USB/Wi-Fi",
                "count": cnt,
                "serial": serial,
                "details": f"Serial: {serial} | Model: {model}",
                "status": "online" if dev.get("state") == "device" else "offline"
            })
    except Exception as e:
        print(f"[StatsManager] Error scanning ADB devices: {e}", file=sys.stderr)

    return adb_list


def scan_over_ip_hosts_info() -> List[Dict[str, Any]]:
    """
    Ping and scan all Over-IP peer hosts stored in ui/db.db ip_hosts table.
    """
    cfg = config_manager.load_config()
    redis_cfg = cfg.get("redis")
    stored_ips = ui_db.get_connection().cursor().execute(
        "SELECT id, ip_address, port, alias, last_seen, is_online FROM ip_hosts ORDER BY id DESC"
    ).fetchall()

    ip_list = []
    for r in stored_ips:
        ip_addr = r["ip_address"]
        port = r["port"]
        alias = r["alias"] or ip_addr

        ping_res = ip_client.ping_host(ip_addr, port=port, redis_cfg=redis_cfg)
        is_online = ping_res.get("online", False)
        song_cnt = ping_res.get("song_count", 0)
        hostname = ping_res.get("hostname") or alias

        ui_db.get_connection().execute(
            "UPDATE ip_hosts SET is_online = ?, last_seen = CURRENT_TIMESTAMP WHERE ip_address = ?",
            (1 if is_online else 0, ip_addr)
        )

        ip_list.append({
            "id": f"ip_{ip_addr}",
            "name": f"Over-IP Peer: {hostname}",
            "type": "Over-IP HTTP",
            "count": song_cnt,
            "ip": ip_addr,
            "port": port,
            "details": f"http://{ip_addr}:{port} | Host: {hostname}",
            "status": "online" if is_online else "offline"
        })

    return ip_list


def get_all_available_devices() -> List[Dict[str, Any]]:
    """
    Combine Local Music folders, connected ADB devices, and Over-IP peer devices.
    """
    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])

    local_songs = song_scanner.scan_songs_from_paths(folders, audio_exts)

    devices = [
        {
            "id": "local",
            "name": "Local Music Folders",
            "type": "Local Storage",
            "count": len(local_songs),
            "details": ", ".join(folders),
            "status": "online"
        }
    ]

    devices.extend(scan_adb_devices_info())
    devices.extend(scan_over_ip_hosts_info())

    return devices


def get_dashboard_summary_stats() -> Dict[str, Any]:
    """
    Compute complete dashboard metrics for Flask Web UI.
    """
    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])

    # 1. Local Music Songs & Duplicates
    local_songs = song_scanner.scan_songs_from_paths(folders, audio_exts)
    duplicate_info = detect_duplicate_songs(local_songs)

    # 2. Combined Available Devices
    device_counts = get_all_available_devices()

    # 3. Synced Tracks Count (ui/db.db)
    synced_records = ui_db.get_all_synced_records()
    synced_count = len(synced_records)

    # 4. Hidden Songs Count (ui/db.db)
    hidden_records = ui_db.get_all_hidden_records()
    hidden_count = len(hidden_records)

    return {
        "total_local_songs": len(local_songs),
        "device_counts": device_counts,
        "synced_count": synced_count,
        "hidden_count": hidden_count,
        "duplicates_count": duplicate_info["total_duplicates"],
        "duplicate_clusters_count": duplicate_info["cluster_count"],
        "folders": folders,
        "timestamp": os.popen("date '+%Y-%m-%d %H:%M:%S'").read().strip()
    }
