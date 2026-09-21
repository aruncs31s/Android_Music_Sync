"""
Interactive Over-IP Synchronization Workflow.
Handles IP prompting & SQLite persistence, online host status pinging,
remote song acquisition (sorted by mtime), and Ranger dual-pane interactive sync over HTTP.
"""
import os
import sys
from typing import List, Dict, Any, Optional

import utils.config_manager as config_manager
import database.hide_list_db as hide_list_db
import database.redis_cache as redis_cache
import over_ip.db as ip_db
import over_ip.client as ip_client
import over_ip.song_scanner as song_scanner
import tui.ranger_reverse_sync_tui as ranger_reverse_sync_tui
from utils import get_logger
logger = get_logger()


def select_or_input_ip_host(
    target_ip: Optional[str] = None,
    redis_cfg: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Acquire peer IP address.
    Prompts if none provided, saves to SQLite ip_hosts, pings hosts for online status,
    and returns selected online target host info.
    """
    if target_ip:
        ip_db.add_ip_host(target_ip)

    stored_hosts = ip_db.get_stored_ip_hosts()

    if not stored_hosts and not target_ip:
        logger.info("=== Over-IP HTTP Synchronization ===")
        try:
            user_ip = input("Enter remote device IP address (e.g. 192.168.1.50): ").strip()
            if not user_ip:
                logger.info("No IP address entered. Exiting.")
                return None
            ip_db.add_ip_host(user_ip)
            stored_hosts = ip_db.get_stored_ip_hosts()
        except (KeyboardInterrupt, EOFError):
            logger.info("Aborted.")
            return None

    logger.info("[Over-IP] Checking online status of saved IP hosts...")
    online_hosts = []

    for idx, host in enumerate(stored_hosts, 1):
        ip_addr = host["ip_address"]
        port = host.get("port", 5000)
        ping_res = ip_client.ping_host(ip_addr, port=port, redis_cfg=redis_cfg)

        status_str = "ONLINE" if ping_res["online"] else "OFFLINE"
        host_name = ping_res.get("hostname", "Unknown")
        song_cnt = ping_res.get("song_count", 0)

        logger.info(f"  [{idx}] {ip_addr}:{port} | Host: {host_name} | Status: [{status_str}] ({song_cnt} songs)")

        if ping_res["online"]:
            host_info = dict(host)
            host_info.update(ping_res)
            online_hosts.append(host_info)

    if not online_hosts:
        logger.warning("No online Over-IP peer hosts found. Make sure Flask API server is running on target (`python3 app.py --serve-ip`).")
        try:
            retry_ip = input("Enter a new IP address to add & try (or press Enter to exit): ").strip()
            if retry_ip:
                ip_db.add_ip_host(retry_ip)
                return select_or_input_ip_host(target_ip=retry_ip, redis_cfg=redis_cfg)
        except (KeyboardInterrupt, EOFError):
            pass
        return None

    if len(online_hosts) == 1:
        selected = online_hosts[0]
        logger.info(f"Connected to online peer host: {selected['ip']}:{selected['port']} ({selected['hostname']})")
        return selected

    logger.info("Multiple online hosts detected:")
    for idx, h in enumerate(online_hosts, 1):
        logger.info(f"  [{idx}] {h['ip']}:{h['port']} ({h['hostname']}) - {h['song_count']} songs")

    try:
        ans = input(f"Select host number [1-{len(online_hosts)}] (default 1): ").strip()
        idx_choice = int(ans) if ans.isdigit() else 1
        if 1 <= idx_choice <= len(online_hosts):
            return online_hosts[idx_choice - 1]
    except (KeyboardInterrupt, EOFError):
        pass

    return online_hosts[0]


def run_over_ip_workflow(
    target_ip: Optional[str] = None,
    interactive: bool = True,
    config_path: Optional[str] = None,
    redis_cfg: Optional[Dict[str, Any]] = None,
    refresh_cache: bool = False,
    show_hidden: bool = False
):
    """
    Run complete Over-IP HTTP sync workflow.
    """
    cfg = config_manager.load_config(config_path)
    local_folders = config_manager.get_local_sync_folders(cfg)
    target_folder = local_folders[0] if local_folders else "/home/aruncs/Music"
    audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])

    if not redis_cfg:
        redis_cfg = cfg.get("redis")

    # Step 1: Select/Ping online target host
    host_info = select_or_input_ip_host(target_ip=target_ip, redis_cfg=redis_cfg)
    if not host_info:
        sys.exit(1)

    peer_ip = host_info["ip"]
    peer_port = host_info.get("port", 5000)
    device_serial = f"IP:{peer_ip}"

    # Step 2: Acquire songs from remote Flask server (sorted by mtime)
    logger.info(f"[Over-IP] Acquiring song library from {peer_ip}:{peer_port}...")
    remote_songs = ip_client.get_remote_songs(peer_ip, port=peer_port, redis_cfg=redis_cfg, refresh=refresh_cache)

    if not remote_songs:
        logger.info(f"[Over-IP] No songs returned from peer host {peer_ip}:{peer_port}.")
        sys.exit(0)

    logger.info(f"[Over-IP] Fetched {len(remote_songs)} songs from {peer_ip} (sorted by modification time).")

    # Step 3: Scan local folders & compare
    local_songs = song_scanner.scan_songs_from_paths(local_folders, audio_exts)
    local_filename_set = set(s["filename"].lower() for s in local_songs)

    # Filter out files present locally or in SQLite hide list
    hidden_paths_set = set() if show_hidden else hide_list_db.get_hidden_paths_set()

    missing_from_local = []
    for s in remote_songs:
        fn = s.get("filename") or os.path.basename(s.get("filepath", ""))
        rel_path = s.get("filepath", "")
        if fn.lower() not in local_filename_set and rel_path not in hidden_paths_set:
            missing_from_local.append(s)

    logger.info(f"[Over-IP] Found {len(missing_from_local)} missing songs on local system available on peer {peer_ip}.")

    if not missing_from_local:
        logger.info("[Over-IP] Local library is fully in sync with peer host!")
        sys.exit(0)

    # Build local file index in the schema expected by the Ranger TUI (title_no_ext/path/filename)
    local_files_for_tui = [
        {
            "filename": s.get("filename"),
            "title_no_ext": os.path.splitext(s.get("filename", ""))[0],
            "path": s.get("filepath") or s.get("_data")
        }
        for s in local_songs
        if s.get("filename")
    ]

    # Transfer callback: download each selected track over HTTP and record it.
    def _pull_over_ip(item: Dict[str, Any]) -> bool:
        remote_path = item.get("filepath") or item.get("_data")
        filename = item.get("filename") or os.path.basename(remote_path or "")
        if not remote_path or not filename:
            return False
        dest_path = os.path.join(target_folder, filename)
        ok = ip_client.download_remote_song(peer_ip, remote_path, dest_path, port=peer_port)
        if ok:
            hide_list_db.add_synced_file(dest_path, filename, device_serial=device_serial, remote_dir=remote_path)
        return ok

    # Step 4: Run Ranger Dual-Pane TUI for selection & HTTP download
    result = ranger_reverse_sync_tui.run_ranger_reverse_sync_tui(
        missing_songs=missing_from_local,
        local_files=local_files_for_tui,
        device_serial=device_serial,
        local_dir=target_folder,
        redis_cfg=redis_cfg,
        pull_callback=_pull_over_ip
    )

    pulled = result.get("pulled", []) if isinstance(result, dict) else list(result or [])
    if not pulled:
        logger.info("[Over-IP] No songs selected for Over-IP sync. Exiting.")
        sys.exit(0)

    # Step 5: Report results (transfers already performed by the TUI callback)
    logger.info(f"[Over-IP] Sync Completed: {len(pulled)}/{len(missing_from_local)} songs downloaded to {target_folder}")
