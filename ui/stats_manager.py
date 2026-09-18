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
import datetime
from collections import defaultdict
from typing import List, Dict, Any

import config_manager
import audio_metadata
import over_ip.song_scanner as song_scanner
import over_ip.client as ip_client
import adb_manager
import ui.db_manager as ui_db
import database.db_manager as central_db
import audio_fingerprint
import song_parser
from utils import get_logger

logger = get_logger()


def detect_duplicate_songs(
    songs: List[Dict[str, Any]],
    use_fingerprint: bool = False,
    progress_cb=None,
) -> Dict[str, Any]:
    """
    Detect duplicate audio files across local music folders.
    If use_fingerprint is True and fpcalc is installed, groups songs by acoustic waveform
    fingerprint first (using SQLite cache), falling back to title+artist and filename matching.
    If fpcalc is missing, sets a warning message and falls back to tag/filename matching.

    Optional progress_cb(msg: str) callback is called for each processed song so callers
    (e.g. the SSE streaming endpoint) can relay live progress to the browser.

    Returns dictionary with total duplicate count, duplicate clusters, fpcalc availability, and warning.
    """
    import time as _time

    def _emit(msg: str):
        """Send a progress message to the SSE callback (if any) and swallow errors."""
        if progress_cb:
            try:
                progress_cb(msg)
            except Exception as cb_err:
                logger.warning(f"[DupScan] progress_cb raised an error: {cb_err}")

    logger.info(f"[DupScan] detect_duplicate_songs called — {len(songs)} song(s), use_fingerprint={use_fingerprint}")

    fpcalc_avail = audio_fingerprint.is_fpcalc_available()
    logger.info(f"[DupScan] fpcalc available: {fpcalc_avail}")
    warning = None

    if use_fingerprint and not fpcalc_avail:
        warning = "Acoustic fingerprinting utility ('fpcalc') is not installed on this system. Falling back to tag & filename matching."
        logger.warning(f"[DupScan] {warning}")
        use_fingerprint = False
        _emit("[WARN]  fpcalc not found — falling back to tag & filename matching")

    clusters = []
    seen_paths = set()
    total_songs = len(songs)

    # ------------------------------------------------------------------ #
    #  Phase 1: Acoustic fingerprint matching (only when fpcalc available)
    # ------------------------------------------------------------------ #
    if use_fingerprint and fpcalc_avail:
        logger.info(f"[DupScan] Phase 1: Acoustic fingerprint scan — {total_songs} song(s)")
        _emit(f"[START] Acoustic fingerprint scan — {total_songs} songs")

        logger.info("[DupScan] Loading cached fingerprint map from database...")
        cached_map = central_db.get_all_cached_fingerprints_map()
        logger.info(f"[DupScan] Loaded {len(cached_map)} cached fingerprint(s)")

        by_fingerprint = defaultdict(list)
        cache_hits = 0
        fp_computed = 0
        fp_failed = 0
        fp_skipped = 0

        for idx, s in enumerate(songs, 1):
            fp_path = s.get("filepath")
            display_name = s.get("filename") or (os.path.basename(fp_path) if fp_path else "unknown")

            if not fp_path or not os.path.isfile(fp_path):
                logger.debug(f"[DupScan] ({idx}/{total_songs}) SKIP (missing file): {fp_path!r}")
                _emit(f"[SKIP]  ({idx}/{total_songs}) {display_name} — file not found")
                fp_skipped += 1
                continue

            try:
                st = os.stat(fp_path)
                fsize = st.st_size
                fmtime = st.st_mtime
            except OSError as e:
                logger.warning(f"[DupScan] ({idx}/{total_songs}) SKIP (stat error): {fp_path!r} — {e}")
                _emit(f"[SKIP]  ({idx}/{total_songs}) {display_name} — stat error")
                fp_skipped += 1
                continue

            cached_entry = cached_map.get(fp_path)
            if (
                cached_entry
                and cached_entry.get("file_size") == fsize
                and abs(cached_entry.get("file_mtime", 0.0) - fmtime) < 1e-3
            ):
                fp = cached_entry.get("fingerprint")
                dur = cached_entry.get("duration")
                logger.debug(f"[DupScan] ({idx}/{total_songs}) CACHE HIT: {display_name}")
                _emit(f"[CACHE] ({idx}/{total_songs}) {display_name}")
                cache_hits += 1
            else:
                logger.info(f"[DupScan] ({idx}/{total_songs}) Running fpcalc on: {display_name}")
                _t0 = _time.monotonic()
                res = audio_fingerprint.generate_audio_fingerprint(fp_path)
                elapsed = _time.monotonic() - _t0

                if res:
                    fp = res["fingerprint"]
                    dur = res["duration"]
                    logger.info(f"[DupScan] ({idx}/{total_songs}) fpcalc OK in {elapsed:.2f}s — saving to cache: {display_name}")
                    central_db.save_cached_fingerprint(fp_path, fsize, fmtime, dur, fp)
                    # Update in-memory map so subsequent songs in this run benefit immediately
                    cached_map[fp_path] = {
                        "filepath": fp_path,
                        "file_size": fsize,
                        "file_mtime": fmtime,
                        "duration": dur,
                        "fingerprint": fp,
                    }
                    _emit(f"[FP]    ({idx}/{total_songs}) {display_name}  ({elapsed:.1f}s)")
                    fp_computed += 1
                else:
                    fp = None
                    dur = None
                    logger.warning(f"[DupScan] ({idx}/{total_songs}) fpcalc returned no result for: {fp_path!r}")
                    _emit(f"[FAIL]  ({idx}/{total_songs}) {display_name} — fpcalc returned no result")
                    fp_failed += 1

            if fp:
                s_copy = dict(s)
                s_copy["audio_fingerprint"] = fp
                s_copy["audio_duration"] = dur
                by_fingerprint[fp].append(s_copy)

        logger.info(
            f"[DupScan] Fingerprint pass done — "
            f"cache hits: {cache_hits}, computed: {fp_computed}, "
            f"failed: {fp_failed}, skipped: {fp_skipped}"
        )

        # Build acoustic clusters from fingerprint groups
        logger.info(f"[DupScan] Building acoustic clusters from {len(by_fingerprint)} unique fingerprint(s)...")
        for fp, song_group in by_fingerprint.items():
            if len(song_group) > 1:
                cluster_paths = set(s.get("filepath") for s in song_group if s.get("filepath"))
                if len(cluster_paths) > 1:
                    cluster_name = None
                    for s in song_group:
                        t = (s.get("title") or "").strip()
                        a = (s.get("artist") or "").strip()
                        if t and t.lower() != "unknown":
                            cluster_name = f"{a} - {t}" if a and a.lower() != "unknown" else t
                            break
                    if not cluster_name:
                        cluster_name = song_group[0].get("filename") or os.path.basename(
                            song_group[0].get("filepath", "Audio Track")
                        )

                    cname = cluster_name.title() if cluster_name else "Acoustic Duplicate Cluster"
                    logger.info(f"[DupScan] Acoustic cluster: '{cname}' — {len(song_group)} song(s)")
                    clusters.append({
                        "cluster_name": cname,
                        "match_type": "audio_fingerprint",
                        "count": len(song_group),
                        "songs": song_group
                    })
                    seen_paths.update(cluster_paths)

        logger.info(f"[DupScan] Acoustic clusters found: {len(clusters)}")
    else:
        logger.info(f"[DupScan] Skipping fingerprint phase (use_fingerprint={use_fingerprint}, fpcalc_avail={fpcalc_avail})")
        _emit(f"[START] Tag & filename matching — {total_songs} songs")

    # ------------------------------------------------------------------ #
    #  Phase 2: Tag (title+artist) and filename matching
    # ------------------------------------------------------------------ #
    logger.info(f"[DupScan] Phase 2: Tag & filename matching on remaining songs (already matched: {len(seen_paths)})")
    by_key = defaultdict(list)
    by_filename = defaultdict(list)

    tag_count = 0
    for idx, s in enumerate(songs, 1):
        filepath = s.get("filepath")
        if filepath and filepath in seen_paths:
            continue

        title = (s.get("title") or "").strip().lower()
        artist = (s.get("artist") or "").strip().lower()
        filename = (s.get("filename") or os.path.basename(s.get("filepath", ""))).strip().lower()

        if not use_fingerprint and (idx == 1 or idx % 25 == 0):
            _emit(f"[TAG]   ({idx}/{total_songs}) processing tag & filename matching...")

        if title and title != "unknown":
            key = f"{artist} - {title}" if artist and artist != "unknown" else title
            by_key[key].append(s)

        if filename:
            by_filename[filename].append(s)

        tag_count += 1

    logger.info(f"[DupScan] Tag/filename pass: {tag_count} song(s) scanned, {len(by_key)} title-key group(s), {len(by_filename)} filename group(s)")
    if not use_fingerprint:
        _emit(f"[INFO]  Grouped {tag_count} songs by metadata tags and filenames")

    new_clusters = 0
    for key, song_group in by_key.items():
        if len(song_group) > 1:
            cluster_paths = set(s.get("filepath") for s in song_group if s.get("filepath"))
            if len(cluster_paths) > 1 and not cluster_paths.issubset(seen_paths):
                logger.info(f"[DupScan] Title/artist cluster: '{key.title()}' — {len(song_group)} song(s)")
                _emit(f"[MATCH] Duplicate: '{key.title()}' ({len(song_group)} copies)")
                clusters.append({
                    "cluster_name": key.title(),
                    "match_type": "title_artist",
                    "count": len(song_group),
                    "songs": song_group
                })
                seen_paths.update(cluster_paths)
                new_clusters += 1

    for fn, song_group in by_filename.items():
        if len(song_group) > 1:
            cluster_paths = set(s.get("filepath") for s in song_group if s.get("filepath"))
            if len(cluster_paths) > 1 and not cluster_paths.issubset(seen_paths):
                logger.info(f"[DupScan] Filename cluster: '{fn}' — {len(song_group)} song(s)")
                _emit(f"[MATCH] Duplicate: '{fn}' ({len(song_group)} copies)")
                clusters.append({
                    "cluster_name": fn,
                    "match_type": "filename",
                    "count": len(song_group),
                    "songs": song_group
                })
                seen_paths.update(cluster_paths)
                new_clusters += 1

    if new_clusters:
        logger.info(f"[DupScan] Tag/filename matching found {new_clusters} new cluster(s)")
        _emit(f"[INFO]  Found {new_clusters} tag/filename cluster(s)")
    else:
        logger.info("[DupScan] Tag/filename matching found no additional clusters")

    # ------------------------------------------------------------------ #
    #  Final summary
    # ------------------------------------------------------------------ #
    total_duplicate_files = sum(len(c["songs"]) - 1 for c in clusters)
    logger.info(
        f"[DupScan] Scan complete — use_fingerprint={use_fingerprint}: "
        f"{len(clusters)} cluster(s), {total_duplicate_files} duplicate file(s)"
    )
    _emit(f"[DONE]  {len(clusters)} cluster(s) found — {total_duplicate_files} duplicate file(s)")

    return {
        "total_duplicates": total_duplicate_files,
        "cluster_count": len(clusters),
        "clusters": clusters,
        "fpcalc_available": fpcalc_avail,
        "warning": warning
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


def scan_over_ip_hosts_info(live_ping: bool = False) -> List[Dict[str, Any]]:
    """
    Ping and scan Over-IP peer hosts stored in database/db.db ip_hosts table.
    If live_ping is False, uses stored last-known online status to avoid blocking page loads.
    """
    cfg = config_manager.load_config()
    redis_cfg = cfg.get("redis")
    stored_ips = ui_db.get_stored_ip_hosts()

    ip_list = []
    for r in stored_ips:
        ip_addr = r["ip_address"]
        port = r["port"]
        alias = r["alias"] or ip_addr
        is_online = bool(r.get("is_online", 0))
        song_cnt = 0
        hostname = alias

        if live_ping:
            ping_res = ip_client.ping_host(ip_addr, port=port, timeout=1.5, redis_cfg=redis_cfg)
            is_online = ping_res.get("online", False)
            song_cnt = ping_res.get("song_count", 0)
            hostname = ping_res.get("hostname") or alias
            ui_db.update_ip_status(ip_addr, is_online)

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


def get_all_available_devices(local_songs_count: Any = None) -> List[Dict[str, Any]]:
    """
    Combine Local Music folders, connected ADB devices, and Over-IP peer devices.
    """
    from repositories import song_repo
    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)

    if local_songs_count is None:
        local_songs = song_repo.get_all_songs()
        local_songs_count = len(local_songs)

    devices = [
        {
            "id": "local",
            "name": "Local Music Folders",
            "type": "Local Storage",
            "count": local_songs_count,
            "details": ", ".join(folders),
            "status": "online"
        }
    ]

    devices.extend(scan_adb_devices_info())
    devices.extend(scan_over_ip_hosts_info(live_ping=False))

    return devices


def get_dashboard_summary_stats() -> Dict[str, Any]:
    """
    Compute complete dashboard metrics for Flask Web UI leveraging Repository caching.
    """
    from repositories import song_repo, hide_repo, device_repo
    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)

    # 1. Local Music Songs & Duplicates (uses Redis cache if available)
    local_songs = song_repo.get_all_songs()
    duplicate_info = song_repo.get_duplicates()

    # 2. Combined Available Devices (reuses local_songs count to eliminate double disk scans)
    device_counts = get_all_available_devices(local_songs_count=len(local_songs))

    # 3. Synced Tracks Count (ui/db.db)
    synced_records = device_repo.get_synced_records()
    synced_count = len(synced_records)

    # 4. Hidden Songs Count (ui/db.db)
    hidden_records = hide_repo.get_all_hidden_records()
    hidden_count = len(hidden_records)

    return {
        "total_local_songs": len(local_songs),
        "device_counts": device_counts,
        "synced_count": synced_count,
        "hidden_count": hidden_count,
        "duplicates_count": duplicate_info["total_duplicates"],
        "duplicate_clusters_count": duplicate_info["cluster_count"],
        "folders": folders,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
