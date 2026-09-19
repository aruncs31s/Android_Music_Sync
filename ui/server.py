"""
Flask Web Interface & Dashboard REST API Server.
Serves dashboard webpage from ui/templates/ and ui/static/,
using ui/db.db SQLite database for storing dashboard states and hide list.
"""
import os
import sys
import json
import socket
import datetime
from typing import Dict, Any
import queue
import threading
from flask import Flask, jsonify, request, send_file, render_template, Response, stream_with_context


import shutil
import config_manager
import over_ip.song_scanner as song_scanner
import ui.db_manager as ui_db
import ui.stats_manager as ui_stats
import hide_list_db
import utils.syncer as syncer
import utils.android.adb.adb_pusher as adb_pusher
import sync_checker
from repositories import song_repo, playlist_repo, hide_repo, device_repo, deleted_repo
from services.stream_service import StreamService
from services.audio_transcoder import AudioTranscoder
import utils.android.poweramp.poweramp_importer as poweramp_importer
from utils import get_logger

logger = get_logger()
# Create Flask app with template and static folders configured inside ui/
ui_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(ui_dir, "templates"),
    static_folder=os.path.join(ui_dir, "static")
)


@app.route("/", methods=["GET"])
def dashboard_index():
    """Render Web Interface Dashboard."""
    return render_template("dashboard.html")


@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """
    Return dashboard metric counts:
    1. Total song counts in each device
    2. Synced counts
    3. Hidden songs count
    4. Duplicates count
    """
    stats = ui_stats.get_dashboard_summary_stats()
    return jsonify(stats)


@app.route("/api/ping", methods=["GET"])
def ping():
    """Heartbeat endpoint for peer online status verification."""
    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    cached = song_repo._cache_get(song_repo.CACHE_KEY_ALL_SONGS)
    song_count = len(cached) if cached is not None else 0

    return jsonify({
        "status": "ok",
        "hostname": socket.gethostname(),
        "song_count": song_count,
        "folders": folders,
        "server_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/api/songs", methods=["GET"])
def get_songs():
    """Acquire local music library songs sorted by mtime."""
    songs = song_repo.get_all_songs()
    return jsonify(songs)


@app.route("/api/duplicates", methods=["GET"])
def get_duplicates():
    """Return duplicate song clusters with optional acoustic fingerprinting."""
    use_fp = request.args.get("fingerprint", "false").lower() in ("true", "1", "yes")
    refresh = request.args.get("refresh", "false").lower() in ("true", "1", "yes")
    dups = song_repo.get_duplicates(force_refresh=refresh, use_fingerprint=use_fp)
    return jsonify(dups)

@app.route("/api/duplicates/stream", methods=["GET"])
def stream_duplicates():
    """
    SSE endpoint — streams live per-song analysis progress to the browser.
    Each event is a JSON object:
      {"type": "log",   "msg": "..."}         — progress line
      {"type": "done",  "result": {...}}       — final duplicate data payload
      {"type": "error", "msg": "..."}         — on exception
    """
    use_fp = request.args.get("fingerprint", "false").lower() in ("true", "1", "yes")
    client_ip = request.remote_addr
    logger.info(f"[SSE] Client {client_ip} opened duplicate analysis stream (fingerprint={use_fp})")

    # Shared queue between the background analysis thread and the SSE generator.
    # Sentinel value None signals the generator that the thread has finished.
    msg_queue = queue.Queue()

    def progress_cb(msg: str):
        """Forward a progress log line from the analysis thread to the SSE queue."""
        logger.debug(f"[SSE] Progress: {msg}")
        msg_queue.put(json.dumps({"type": "log", "msg": msg}))

    def run_analysis():
        logger.info(f"[SSE] Analysis thread started (fingerprint={use_fp})")
        try:
            progress_cb(f"[START] Initializing duplicate scan ({'acoustic audio fingerprinting' if use_fp else 'tag & filename matching'})...")
            progress_cb("[INFO] Scanning configured music library paths...")
            logger.info("[SSE] Fetching song library...")
            songs = song_repo.get_all_songs(force_refresh=True, progress_cb=progress_cb)
            progress_cb(f"[INFO] Loaded {len(songs)} song(s) from local library.")
            logger.info(f"[SSE] Got {len(songs)} songs, starting duplicate detection...")

            if not songs:
                progress_cb("[WARN] No audio tracks found in local folders. Check your config.json sync paths.")

            result = ui_stats.detect_duplicate_songs(
                songs,
                use_fingerprint=use_fp,
                progress_cb=progress_cb,
            )

            logger.info(
                f"[SSE] Detection complete: {result.get('cluster_count', 0)} cluster(s), "
                f"{result.get('total_duplicates', 0)} duplicate file(s)"
            )

            # Write result into the repo cache (optional — silently skipped if Redis is
            # disabled or unavailable) so subsequent /api/duplicates calls are instant.
            try:
                cache_key = f"{song_repo.CACHE_KEY_DUPLICATES}:{'fp' if use_fp else 'tag'}"
                song_repo._cache_set(cache_key, result)
                logger.info(f"[SSE] Cached result under key '{cache_key}'")
            except Exception as cache_err:
                logger.warning(f"[SSE] Cache write skipped (Redis unavailable?): {cache_err}")

            msg_queue.put(json.dumps({"type": "done", "result": result}))
            logger.info("[SSE] Sent 'done' event to client")

        except Exception as exc:
            logger.error(f"[SSE] Analysis thread error: {exc}", exc_info=True)
            msg_queue.put(json.dumps({"type": "error", "msg": str(exc)}))
        finally:
            msg_queue.put(None)  # sentinel — tells generate() to close the stream
            logger.info("[SSE] Analysis thread finished, sentinel enqueued")

    thread = threading.Thread(target=run_analysis, daemon=True, name="dup-sse-analysis")
    thread.start()
    logger.info(f"[SSE] Background analysis thread '{thread.name}' started")

    def generate():
        """SSE generator — yields events from the analysis thread."""
        logger.info(f"[SSE] Generator started for client {client_ip}")
        try:
            yield ": SSE stream open\n\n"
            import time
            last_keepalive = time.time()

            while True:
                try:
                    # Short timeout (0.5s) so events stream with zero delay
                    item = msg_queue.get(timeout=0.5)
                except queue.Empty:
                    # Send a keepalive comment every 10s if queue has been idle
                    now = time.time()
                    if now - last_keepalive >= 10.0:
                        last_keepalive = now
                        yield ": keepalive\n\n"
                    continue

                if item is None:
                    # Sentinel received — analysis thread finished, close stream.
                    logger.info(f"[SSE] Sentinel received, closing stream for {client_ip}")
                    break

                yield f"data: {item}\n\n"

        except GeneratorExit:
            # Client closed the EventSource connection before analysis finished.
            logger.info(f"[SSE] Client {client_ip} disconnected (GeneratorExit)")

        logger.info(f"[SSE] Generator finished for client {client_ip}")

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )



@app.route("/api/hidden", methods=["GET"])
def get_hidden():
    """Return hidden files using HideListRepository."""
    records = hide_repo.get_all_hidden_records()
    return jsonify(records)


@app.route("/api/synced", methods=["GET"])
def get_synced():
    """Return synced tracks history using DeviceRepository."""
    records = device_repo.get_synced_records()
    return jsonify(records)


@app.route("/api/unhide", methods=["POST"])
def unhide_file():
    """Unhide a file path using HideListRepository."""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath")
    if not filepath:
        return jsonify({"error": "Missing filepath parameter"}), 400

    hide_repo.unhide_file(filepath)
    return jsonify({"status": "success", "message": f"Unhid {filepath}"})


@app.route("/api/hide", methods=["POST"])
def hide_file():
    """Hide a file path using HideListRepository."""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath")
    if not filepath:
        return jsonify({"error": "Missing filepath parameter"}), 400

    hide_repo.hide_file(filepath)
    return jsonify({"status": "success", "message": f"Hid {filepath}"})


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Return list of all available devices (Local, ADB, Over-IP)."""
    devices = ui_stats.get_all_available_devices()
    return jsonify(devices)


@app.route("/api/devices/<path:device_id>/songs", methods=["GET"])
def get_device_songs(device_id):
    """Acquire song library for a specific device (Local, ADB, Over-IP)."""
    force_refresh = request.args.get("refresh", "false").lower() == "true"
    data = device_repo.get_device_songs(device_id, force_refresh=force_refresh)
    return jsonify(data)


@app.route("/api/device/songs", methods=["GET"])
def get_device_songs_query():
    """Fallback query endpoint: /api/device/songs?device_id=..."""
    device_id = request.args.get("device_id", "local")
    force_refresh = request.args.get("refresh", "false").lower() == "true"
    data = device_repo.get_device_songs(device_id, force_refresh=force_refresh)
    return jsonify(data)


@app.route("/api/devices/<path:device_id>/songs/stream", methods=["GET"])
@app.route("/api/songs/stream", methods=["GET"])
def stream_device_songs(device_id="local"):
    """
    SSE endpoint — streams live file scanning progress for the Music Library page.
    'refresh=true' forces a full disk/device re-scan (with progress); otherwise
    cached results are streamed back immediately without re-scanning.
    """
    client_ip = request.remote_addr
    force_refresh = request.args.get("refresh", "false").lower() in ("1", "true", "yes")
    logger.info(f"[SSE-Lib] Client {client_ip} opened library scan stream (device={device_id}, refresh={force_refresh})")

    msg_queue = queue.Queue()

    def progress_cb(msg: str):
        logger.debug(f"[SSE-Lib] Progress: {msg}")
        msg_queue.put(json.dumps({"type": "log", "msg": msg}))

    def run_library_scan():
        logger.info(f"[SSE-Lib] Scan thread started for device '{device_id}' (refresh={force_refresh})")
        try:
            progress_cb(f"[START] {'Initializing library scan' if force_refresh else 'Loading cached song library'} for '{device_id}'...")
            data = device_repo.get_device_songs(device_id, force_refresh=force_refresh, progress_cb=progress_cb)
            progress_cb(f"[DONE] Library {'scan' if force_refresh else 'load'} complete — {data.get('count', 0)} song(s) loaded.")
            msg_queue.put(json.dumps({"type": "done", "result": data}))
            logger.info(f"[SSE-Lib] Scan complete for '{device_id}': {data.get('count', 0)} songs")
        except Exception as exc:
            logger.error(f"[SSE-Lib] Scan thread error: {exc}", exc_info=True)
            msg_queue.put(json.dumps({"type": "error", "msg": str(exc)}))
        finally:
            msg_queue.put(None)

    thread = threading.Thread(target=run_library_scan, daemon=True, name="lib-sse-scan")
    thread.start()

    def generate():
        logger.info(f"[SSE-Lib] Generator started for {client_ip}")
        try:
            yield ": SSE stream open\n\n"
            import time
            last_keepalive = time.time()
            while True:
                try:
                    item = msg_queue.get(timeout=0.5)
                except queue.Empty:
                    now = time.time()
                    if now - last_keepalive >= 10.0:
                        last_keepalive = now
                        yield ": keepalive\n\n"
                    continue
                if item is None:
                    break
                yield f"data: {item}\n\n"
        except GeneratorExit:
            logger.info(f"[SSE-Lib] Client {client_ip} disconnected")

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/api/devices/scan-adb", methods=["POST"])
def scan_adb_devices():
    """Trigger live ADB device discovery scan."""
    adb_devs = ui_stats.scan_adb_devices_info()
    return jsonify({"status": "success", "devices": adb_devs})


@app.route("/api/devices/scan-ip", methods=["POST"])
def scan_ip_hosts():
    """Trigger live UDP self-discovery and ping scan of Over-IP peer hosts."""
    try:
        from over_ip.discovery import PeerDiscoveryService
        PeerDiscoveryService.get_instance().broadcast_discover(timeout=1.2)
    except Exception as e:
        logger.warning(f"[Discovery] Error during scan-ip discovery probe: {e}")

    ip_devs = ui_stats.scan_over_ip_hosts_info(live_ping=True)
    return jsonify({"status": "success", "devices": ip_devs})


# --- MUSIC FOLDER SYNC (LOCAL -> ADB DEVICE) API ENDPOINTS ---

@app.route("/api/sync/devices", methods=["GET"])
def sync_devices():
    """Return connected ADB devices suitable for folder sync target selection."""
    adb_devs = ui_stats.scan_adb_devices_info()
    online = [d for d in adb_devs if d.get("status") == "online"]
    return jsonify({"status": "success", "devices": online})


@app.route("/api/sync/preview", methods=["GET"])
def sync_preview():
    """
    Compare local music folders against a target ADB device.
    Returns already-present tracks, tracks to sync, and device song count.
    """
    serial = request.args.get("serial", "").strip()
    force = request.args.get("force", "false").lower() in ("1", "true", "yes")
    if not serial:
        return jsonify({"error": "Missing serial parameter"}), 400

    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    remote_dir = cfg.get("remote_adb_folder", "/storage/emulated/0/Music/ADB")
    audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])
    redis_cfg = cfg.get("redis")

    local_files = []
    seen_paths = set()
    for folder in folders:
        for item in syncer.scan_local_music_folder(folder, audio_exts):
            if item["path"] not in seen_paths:
                seen_paths.add(item["path"])
                local_files.append(item)

    if not local_files:
        return jsonify({
            "status": "success",
            "serial": serial,
            "remote_dir": remote_dir,
            "local_folders": folders,
            "local_count": 0,
            "already_present": [],
            "to_sync": [],
            "device_songs_count": 0
        })

    try:
        already_present, to_sync, device_songs = syncer.compare_local_files_with_device(
            local_files,
            serial,
            remote_dir,
            redis_cfg=redis_cfg,
            refresh_cache=False,
            show_hidden=False
        )
    except Exception as e:
        logger.error(f"[Web Sync] Error comparing files with device: {e}")
        return jsonify({"error": f"Failed to compare files with device: {e}"}), 500

    if force:
        to_sync = local_files

    already_serializable = []
    for item in already_present:
        loc = item.get("local") or {}
        dm = item.get("device_match") or {}
        already_serializable.append({
            "filename": loc.get("filename"),
            "rel_path": loc.get("rel_path"),
            "size_formatted": loc.get("size_formatted"),
            "match_reason": item.get("match_reason", ""),
            "device_title": dm.get("title", ""),
            "device_path": dm.get("_data", "")
        })

    logger.info(f"[Web Sync] Preview for [{serial}]: {len(local_files)} local, "
                f"{len(already_serializable)} already present, {len(to_sync)} to sync.")

    return jsonify({
        "status": "success",
        "serial": serial,
        "remote_dir": remote_dir,
        "local_folders": folders,
        "local_count": len(local_files),
        "already_present": already_serializable,
        "to_sync": to_sync,
        "device_songs_count": len(device_songs)
    })


@app.route("/api/sync/run", methods=["POST"])
def sync_run():
    """
    Push a list of local filepaths to a target device (ADB or Over-IP peer).
    Supports optional on-the-fly audio downconversion via target_bitrate.
    """
    data = request.get_json(silent=True) or {}
    device_id = data.get("device_id", "").strip()
    serial = data.get("serial", "").strip()
    if not device_id and serial:
        device_id = f"adb_{serial}"
    elif not device_id:
        device_id = "local"

    file_paths = data.get("files") or []
    remote_dir = data.get("remote_dir") or ""
    target_bitrate = data.get("target_bitrate")
    if target_bitrate:
        try:
            target_bitrate = int(target_bitrate)
        except (TypeError, ValueError):
            target_bitrate = None

    if not file_paths or not isinstance(file_paths, list):
        return jsonify({"error": "No files selected to sync"}), 400

    results = []
    success_count = 0
    failed_count = 0

    for fp in file_paths:
        fp = os.path.abspath(fp)
        push_res = device_repo.push_song_to_device(
            device_id=device_id,
            local_filepath=fp,
            remote_dir=remote_dir,
            target_bitrate=target_bitrate
        )
        ok = (push_res.get("status") == "success")
        if ok:
            success_count += 1
            results.append({
                "filepath": fp,
                "success": True,
                "dest_path": push_res.get("dest_path", ""),
                "transcoded": push_res.get("transcoded", False),
                "target_bitrate": push_res.get("target_bitrate")
            })
        else:
            failed_count += 1
            results.append({
                "filepath": fp,
                "success": False,
                "error": push_res.get("message", "Sync failed")
            })

    logger.info(f"[Web Sync] Pushed {success_count}/{len(file_paths)} files to [{device_id}] ({remote_dir}).")

    return jsonify({
        "status": "success",
        "device_id": device_id,
        "serial": serial,
        "remote_dir": remote_dir,
        "pushed": success_count,
        "failed": failed_count,
        "total": len(file_paths),
        "results": results
    })


@app.route("/api/sync/check-song", methods=["GET"])
def sync_check_song():
    """
    Check if a specific local song exists on the destination device,
    and find similar songs using fuzzy matching and audio properties.
    """
    filepath = request.args.get("filepath", "").strip()
    device_id = request.args.get("device_id", "").strip()
    if not filepath or not device_id:
        return jsonify({"error": "Missing filepath or device_id parameter"}), 400

    result = sync_checker.check_song_on_device(filepath, device_id)
    if result.get("status") == "error":
        return jsonify({"error": result.get("message")}), result.get("code", 500)

    return jsonify(result)


@app.route("/api/sync/song", methods=["POST"])
def sync_single_song():
    """
    Push/sync a single audio track to a target device (ADB or Over-IP peer).
    Supports optional target_bitrate downconversion.
    """
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath", "").strip()
    device_id = data.get("device_id", "").strip()
    remote_dir = data.get("remote_dir") or None
    force = bool(data.get("force", False))
    target_bitrate = data.get("target_bitrate")
    if target_bitrate:
        try:
            target_bitrate = int(target_bitrate)
        except (TypeError, ValueError):
            target_bitrate = None

    if not filepath or not device_id:
        return jsonify({"error": "Missing filepath or device_id parameter"}), 400

    result = device_repo.push_song_to_device(
        device_id=device_id,
        local_filepath=filepath,
        remote_dir=remote_dir,
        force=force,
        target_bitrate=target_bitrate
    )
    if result.get("status") == "error":
        return jsonify({"error": result.get("message")}), result.get("code", 500)

    return jsonify(result)



@app.route("/api/devices/add-ip", methods=["POST"])
def add_ip_host():
    """Add a new Over-IP peer host address to ui/db.db and ping it."""
    data = request.get_json(silent=True) or {}
    ip_addr = data.get("ip_address") or data.get("ip")
    port = int(data.get("port", 5000))
    alias = data.get("alias", "")

    if not ip_addr:
        return jsonify({"error": "Missing ip_address parameter"}), 400

    device_repo.add_ip_host(ip_addr, port, alias)
    ip_stats_res = ui_stats.scan_over_ip_hosts_info()

    return jsonify({
        "status": "success",
        "message": f"Added Over-IP peer host {ip_addr}:{port}",
        "devices": ip_stats_res
    })


@app.route("/api/song/delete", methods=["POST"])
def delete_song():
    """
    Safely delete audio file from local disk or target device (ADB / Over-IP).
    Removes file from disk/device and cleans up database & cache references.
    """
    data = request.get_json(silent=True) or {}
    file_path = data.get("filepath") or request.form.get("filepath") or request.args.get("filepath")
    device_id = data.get("device_id") or request.form.get("device_id") or request.args.get("device_id") or "local"
    song_id = data.get("song_id") or request.form.get("song_id") or request.args.get("song_id")
    filename = data.get("filename") or request.form.get("filename") or request.args.get("filename")

    if not file_path:
        return jsonify({"error": "Missing filepath parameter"}), 400

    result = device_repo.delete_device_song(
        device_id=device_id,
        filepath=file_path,
        song_id=song_id,
        filename=filename
    )
    if result.get("status") == "error":
        return jsonify({"error": result.get("message")}), result.get("code", 500)

    return jsonify(result)


@app.route("/api/songs/delete-batch", methods=["POST"])
def delete_songs_batch():
    """
    Batch delete multiple audio files from local disk or target device.
    """
    data = request.get_json(silent=True) or {}
    filepaths = data.get("filepaths") or []
    device_id = data.get("device_id") or "local"

    if not filepaths:
        return jsonify({"error": "No filepaths provided"}), 400

    result = device_repo.delete_device_songs_batch(
        device_id=device_id,
        filepaths=filepaths
    )
    if result.get("status") == "error":
        return jsonify({"error": result.get("message")}), result.get("code", 500)

    return jsonify(result)


@app.route("/api/deleted", methods=["GET"])
def get_deleted_songs():
    """Return deleted songs history (files kept in repo-local trash)."""
    return jsonify(deleted_repo.get_deleted_songs())


@app.route("/api/deleted/restore", methods=["POST"])
def restore_deleted_song():
    """Move a deleted song back to its original filepath."""
    data = request.get_json(silent=True) or {}
    record_id = data.get("id")
    if record_id is None:
        return jsonify({"error": "Missing id parameter"}), 400

    try:
        record_id = int(record_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid id parameter"}), 400

    result = deleted_repo.restore_deleted_song(record_id)
    if result.get("status") == "error":
        return jsonify({"error": result.get("message")}), result.get("code", 500)

    return jsonify(result)


@app.route("/api/deleted/clear", methods=["POST"])
def clear_deleted_songs():
    """Permanently remove all trash files and clear deleted songs history."""
    return jsonify(deleted_repo.clear_deleted_history())



@app.route("/api/song/stream", methods=["GET"])
def stream_song():
    """
    Download/stream audio file with Range seeking support (RFC 7233).
    Supports local files as well as remote Over-IP companion devices.
    """
    file_path = request.args.get("filepath") or request.args.get("file")
    device_id = request.args.get("device_id", "local").strip()
    range_header = request.headers.get("Range")
    bitrate_param = request.args.get("bitrate") or request.args.get("target_bitrate")

    if not file_path:
        return jsonify({"error": "Missing filepath parameter"}), 400

    # Over-IP Peer device
    if device_id.startswith("ip_") or device_id.startswith("ip:") or device_id.startswith("http://") or device_id.startswith("https://"):
        return StreamService.stream_remote_peer(device_id, file_path, range_header=range_header)

    # Check for on-the-fly audio downconversion
    if bitrate_param and str(bitrate_param).isdigit():
        target_br = int(bitrate_param)
        if AudioTranscoder.is_ffmpeg_available() and AudioTranscoder.needs_downconversion(file_path, target_br):
            trans_res = AudioTranscoder.transcode_audio(file_path, target_br)
            if trans_res.success and os.path.isfile(trans_res.output_path):
                resp = StreamService.stream_local_file(trans_res.output_path, range_header=range_header)
                out_to_clean = trans_res.output_path
                @resp.call_on_close
                def _cleanup_transcode():
                    if os.path.exists(out_to_clean):
                        try:
                            os.remove(out_to_clean)
                        except Exception:
                            pass
                return resp

    # Local file streaming
    return StreamService.stream_local_file(file_path, range_header=range_header)


@app.route("/api/song/upload", methods=["POST"])
def upload_song():
    """
    Receive uploaded audio file from peer device over HTTP.
    Saves file into the primary configured local music folder.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file payload in request"}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return jsonify({"error": "Empty filename"}), 400

    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    target_folder = folders[0] if folders else os.path.expanduser("~/Music")

    os.makedirs(target_folder, exist_ok=True)
    dest_path = os.path.join(target_folder, uploaded_file.filename)

    uploaded_file.save(dest_path)
    song_repo.invalidate_all_song_caches()

    return jsonify({
        "status": "success",
        "message": f"Saved {uploaded_file.filename}",
        "dest_path": dest_path
    })


@app.route("/api/devices/<path:device_id>/upload", methods=["POST"])
def upload_to_device(device_id):
    """
    Upload one or more audio files directly from client browser to target device (Over-IP peer or ADB).
    Supports optional on-the-fly target_bitrate downconversion.
    """
    device_id = device_id.strip()
    files = request.files.getlist("files")
    if not files and "file" in request.files:
        files = [request.files["file"]]

    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    target_bitrate = request.form.get("target_bitrate")
    if target_bitrate:
        try:
            target_bitrate = int(target_bitrate)
        except (TypeError, ValueError):
            target_bitrate = None

    uploaded_results = []
    success_count = 0
    import tempfile

    for f in files:
        if not f.filename:
            continue
        clean_name = os.path.basename(f.filename)
        ext = os.path.splitext(clean_name)[1] or ".mp3"
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        tmp_path = tmp.name
        try:
            f.save(tmp_path)
            tmp.close()

            push_res = device_repo.push_song_to_device(
                device_id=device_id,
                local_filepath=tmp_path,
                target_bitrate=target_bitrate
            )
            if push_res.get("status") == "success":
                success_count += 1
                uploaded_results.append({
                    "filename": clean_name,
                    "success": True,
                    "transcoded": push_res.get("transcoded", False),
                    "target_bitrate": push_res.get("target_bitrate")
                })
            else:
                uploaded_results.append({
                    "filename": clean_name,
                    "success": False,
                    "error": push_res.get("message", "Upload failed")
                })
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    return jsonify({
        "status": "success" if success_count > 0 else "error",
        "device_id": device_id,
        "uploaded": success_count,
        "total": len(files),
        "results": uploaded_results
    })


@app.route("/api/song/transcode", methods=["POST"])
def transcode_local_song():
    """
    Downconvert a local audio file to target bitrate (e.g. 128, 192, 256).
    """
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath", "").strip()
    target_bitrate = data.get("target_bitrate")
    replace_original = bool(data.get("replace_original", False))

    if not filepath:
        return jsonify({"error": "Missing filepath parameter"}), 400

    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filepath}"}), 404

    try:
        target_bitrate = int(target_bitrate)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid target_bitrate parameter"}), 400

    abs_path = os.path.abspath(filepath)
    if replace_original:
        tmp_out = f"{abs_path}.transcoded.mp3"
        res = AudioTranscoder.transcode_audio(abs_path, target_bitrate, output_path=tmp_out)
        if not res.success:
            return jsonify({"error": res.error or "Transcode failed"}), 500
        # Backup original to .orig.bak and replace
        bak_path = f"{abs_path}.orig.bak"
        shutil.move(abs_path, bak_path)
        shutil.move(tmp_out, abs_path)
        final_path = abs_path
    else:
        base, ext = os.path.splitext(abs_path)
        final_path = f"{base}_{target_bitrate}k.mp3"
        res = AudioTranscoder.transcode_audio(abs_path, target_bitrate, output_path=final_path)
        if not res.success:
            return jsonify({"error": res.error or "Transcode failed"}), 500

    # Update SQLite local_songs record
    try:
        from over_ip.song_scanner import format_mtime
        st = os.stat(final_path)
        meta = audio_metadata.extract_audio_metadata(final_path)
        clean_name = os.path.basename(final_path)
        title = meta.get("title") or os.path.splitext(clean_name)[0]
        artist = meta.get("artist") or "Unknown"
        album = meta.get("album") or "Unknown"
        new_record = {
            "filepath": final_path,
            "filename": clean_name,
            "title": title,
            "artist": artist,
            "album": album,
            "size": st.st_size,
            "size_formatted": meta.get("size", f"{st.st_size / (1024*1024):.1f} MB"),
            "mtime": st.st_mtime,
            "mtime_str": format_mtime(st.st_mtime),
            "ctime": getattr(st, "st_birthtime", st.st_ctime),
            "ctime_str": format_mtime(getattr(st, "st_birthtime", st.st_ctime)),
            "duration_sec": 0.0,
            "duration_formatted": meta.get("duration", "00:00"),
            "bitrate_kbps": f"{target_bitrate} kbps",
            "bitrate_val": target_bitrate,
            "sample_rate_hz": meta.get("sample_rate", "Unknown"),
            "channels": meta.get("channels", "Stereo"),
            "codec": meta.get("codec", "mp3"),
            "searchable_text": f"{title} {artist} {album} {clean_name}".lower()
        }
        ui_db.save_local_songs([new_record], purge_missing=False)
    except Exception as e:
        logger.warning(f"[Server] Note updating transcode in SQLite: {e}")

    from repositories import song_repo
    song_repo.invalidate_all_song_caches()

    return jsonify({
        "status": "success",
        "original_path": abs_path,
        "output_path": final_path,
        "original_bitrate": res.original_bitrate,
        "new_bitrate": target_bitrate,
        "original_size": res.original_size,
        "new_size": res.new_size,
        "message": f"Successfully downconverted to {target_bitrate} kbps."
    })


# --- PLAYLIST API ENDPOINTS ---

@app.route("/api/playlists", methods=["GET"])
def get_playlists():
    """Retrieve all playlists with track counts using PlaylistRepository."""
    playlists = playlist_repo.get_playlists()
    return jsonify(playlists)


@app.route("/api/playlists/create", methods=["POST"])
def create_playlist():
    """Create a new playlist using PlaylistRepository."""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Playlist name is required"}), 400

    result = playlist_repo.create_playlist(name)
    if not result:
        return jsonify({"error": "Failed to create playlist or name already exists"}), 400

    return jsonify({"status": "success", "playlist": result})


@app.route("/api/playlists/delete", methods=["POST"])
def delete_playlist():
    """Delete a playlist using PlaylistRepository."""
    data = request.get_json(silent=True) or {}
    playlist_id = data.get("playlist_id")
    if not playlist_id:
        return jsonify({"error": "Missing playlist_id parameter"}), 400

    success = playlist_repo.delete_playlist(int(playlist_id))
    if not success:
        return jsonify({"error": "Failed to delete playlist"}), 500

    return jsonify({"status": "success", "message": f"Deleted playlist {playlist_id}"})


@app.route("/api/playlists/<int:playlist_id>/tracks", methods=["GET"])
def get_playlist_tracks(playlist_id: int):
    """Retrieve tracks for a playlist with metadata using PlaylistRepository."""
    full_tracks = playlist_repo.get_playlist_tracks(playlist_id)
    return jsonify(full_tracks)


@app.route("/api/playlists/<int:playlist_id>/add-track", methods=["POST"])
def add_track_to_playlist(playlist_id: int):
    """Add a track to a playlist using PlaylistRepository."""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath")
    if not filepath:
        return jsonify({"error": "Missing filepath parameter"}), 400

    filepath = os.path.abspath(filepath)
    success = playlist_repo.add_track_to_playlist(playlist_id, filepath)
    if not success:
        return jsonify({"error": "Failed to add track to playlist"}), 500

    return jsonify({"status": "success", "message": f"Added track to playlist {playlist_id}"})


@app.route("/api/playlists/<int:playlist_id>/remove-track", methods=["POST"])
def remove_track_from_playlist(playlist_id: int):
    """Remove a track from a playlist using PlaylistRepository."""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath")
    if not filepath:
        return jsonify({"error": "Missing filepath parameter"}), 400

    filepath = os.path.abspath(filepath)
    success = playlist_repo.remove_track_from_playlist(playlist_id, filepath)
    if not success:
        return jsonify({"error": "Failed to remove track from playlist"}), 500

    return jsonify({"status": "success", "message": f"Removed track from playlist {playlist_id}"})


@app.route("/api/playlists/<int:playlist_id>/absent", methods=["GET"])
def get_playlist_absent(playlist_id: int):
    """Retrieve absent tracks for a specific playlist from SQLite."""
    absent = playlist_repo.get_absent_tracks(playlist_id)
    return jsonify(absent)


@app.route("/api/playlists/absent-all", methods=["GET"])
def get_all_absent_tracks():
    """Retrieve absent tracks across all playlists from SQLite."""
    absent = playlist_repo.get_absent_tracks()
    return jsonify(absent)


@app.route("/api/playlists/<int:playlist_id>/resolve", methods=["POST"])
def resolve_playlist_track(playlist_id: int):
    """Resolve an absent track in a playlist with a local filepath."""
    data = request.get_json(silent=True) or {}
    resolved_filepath = data.get("resolved_filepath")
    original_path = data.get("original_path") or data.get("filepath", "")
    track_id = data.get("track_id")
    title = data.get("title")
    artist = data.get("artist")
    album = data.get("album")

    if not resolved_filepath or (not original_path and not track_id):
        return jsonify({"error": "Missing resolved_filepath or original_path/track_id"}), 400

    resolved_filepath = os.path.abspath(resolved_filepath)
    success = playlist_repo.resolve_absent_track(
        playlist_id=playlist_id,
        original_path=original_path,
        resolved_filepath=resolved_filepath,
        title=title,
        artist=artist,
        album=album,
        track_id=track_id
    )
    if not success:
        return jsonify({"error": "Failed to resolve track in database"}), 500

    return jsonify({"status": "success", "message": "Track resolved successfully"})


# --- POWERAMP IMPORT API ENDPOINTS ---

_last_poweramp_report: Optional[Dict[str, Any]] = None

@app.route("/api/poweramp/import", methods=["POST"])
def import_poweramp():
    """
    Import Poweramp playlists & ratings from uploaded file or local file path.
    Supports zip archives (with or without .zip extension), lists-export SQLite DBs, and directories.
    """
    global _last_poweramp_report
    try:
        # Check if file was uploaded via multipart/form-data
        if "file" in request.files:
            file = request.files["file"]
            if not file.filename:
                return jsonify({"error": "No selected file"}), 400
            report = poweramp_importer.import_poweramp_backup(file)
            _last_poweramp_report = report
            return jsonify(report)

        # Check JSON payload for file_path
        data = request.get_json(silent=True) or {}
        file_path = data.get("file_path", "").strip()
        if not file_path:
            return jsonify({"error": "No file uploaded or file_path provided"}), 400

        report = poweramp_importer.import_poweramp_backup(file_path)
        _last_poweramp_report = report
        return jsonify(report)
    except Exception as e:
        logger.error(f"[PowerampImport] Failed to import Poweramp backup: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/poweramp/status", methods=["GET"])
def get_poweramp_status():
    """Return the cached report of the last Poweramp import, or load persistent absent tracks from SQLite."""
    global _last_poweramp_report
    if _last_poweramp_report:
        return jsonify({"has_report": True, "report": _last_poweramp_report})

    db_absent = playlist_repo.get_absent_tracks()
    if db_absent:
        synthetic_report = {
            "status": "success",
            "total_playlists": len(playlist_repo.get_playlists()),
            "absent_tracks_count": len(db_absent),
            "absent_songs": db_absent,
            "persistent": True
        }
        return jsonify({"has_report": True, "report": synthetic_report})

    return jsonify({"has_report": False, "report": None})


@app.route("/api/poweramp/export-absent", methods=["GET", "POST"])
def export_poweramp_absent_songs():
    """
    Generate and download a formatted text file report of absent songs.
    Can use absent_songs list from POST JSON, or fallback to the last import report or DB.
    """
    global _last_poweramp_report
    absent_list = []

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        absent_list = data.get("absent_songs", [])

    if not absent_list:
        if _last_poweramp_report:
            absent_list = _last_poweramp_report.get("absent_songs", [])
        if not absent_list:
            absent_list = playlist_repo.get_absent_tracks()

    lines = []
    lines.append("================================================================================")
    lines.append(" POWERAMP PLAYLIST IMPORT - ABSENT SONGS REPORT")
    lines.append(f" Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f" Total Absent Songs: {len(absent_list)}")
    lines.append("================================================================================\n")

    # Group by playlist
    by_playlist: Dict[str, List[Dict[str, Any]]] = {}
    for item in absent_list:
        pl_name = item.get("playlist_name", "Unknown")
        by_playlist.setdefault(pl_name, []).append(item)

    for pl_name, items in sorted(by_playlist.items()):
        lines.append(f"Playlist: {pl_name} ({len(items)} missing)")
        lines.append("-" * 60)
        for it in items:
            title = it.get("readable_name") or it.get("filename")
            orig = it.get("original_path", "")
            lines.append(f"  • {title}")
            if orig and orig != title:
                lines.append(f"    Path: {orig}")
        lines.append("")

    report_text = "\n".join(lines)
    return Response(
        report_text,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=poweramp_absent_songs.txt"}
    )



@app.route("/api/poweramp/search-library", methods=["GET"])
def poweramp_search_library():
    """
    Fuzzy-search the local song library for a given query string.
    Returns top N matching songs with filepath, title, artist, album.

    Query params:
      q   - search term (readable_name / filename to match)
      n   - max results (default 8, max 20)
    """
    q = request.args.get("q", "").strip()
    max_results = min(int(request.args.get("n", "8")), 20)

    if not q:
        return jsonify([])

    clean_q = poweramp_importer.clean_string_for_matching(q)
    q_lower = q.lower()

    songs = song_repo.get_all_songs()
    scored: List[Dict[str, Any]] = []

    for s in songs:
        title = s.get("title", "") or ""
        filename = s.get("filename", "") or ""
        artist = s.get("artist", "") or ""
        filepath = s.get("filepath", s.get("_data", "")) or ""

        score = 0

        # Exact / startswith matches → high score
        title_l = title.lower()
        fn_l = filename.lower()

        if title_l == q_lower or fn_l == q_lower:
            score += 100
        elif title_l.startswith(q_lower) or fn_l.startswith(q_lower):
            score += 70
        elif q_lower in title_l or q_lower in fn_l:
            score += 40

        # Clean-string matching
        clean_title = poweramp_importer.clean_string_for_matching(title)
        clean_fn = poweramp_importer.clean_string_for_matching(filename)

        if clean_title == clean_q:
            score += 60
        elif clean_title.startswith(clean_q):
            score += 30
        elif clean_q and clean_q in clean_title:
            score += 20

        if clean_fn == clean_q:
            score += 50
        elif clean_fn.startswith(clean_q):
            score += 25
        elif clean_q and clean_q in clean_fn:
            score += 15

        # Word-level overlap scoring
        q_words = set(clean_q.split())
        title_words = set(clean_title.split())
        fn_words = set(clean_fn.split())
        common = q_words & (title_words | fn_words)
        if q_words:
            score += int(80 * len(common) / len(q_words))

        if score > 0:
            scored.append({
                "score": score,
                "filepath": filepath,
                "title": title or os.path.splitext(filename)[0],
                "artist": artist or "Unknown",
                "album": s.get("album", "") or "Unknown",
                "filename": filename,
                "duration_formatted": s.get("duration_formatted", ""),
                "size_formatted": s.get("size_formatted", "")
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    results = [{"filepath": r["filepath"], "title": r["title"], "artist": r["artist"],
                "album": r["album"], "filename": r["filename"],
                "duration_formatted": r["duration_formatted"],
                "size_formatted": r["size_formatted"]}
               for r in scored[:max_results]]

    return jsonify(results)


def start_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Start Flask Web Dashboard server."""
    logger.info(f"[Web UI Dashboard] Launching web interface on http://{host}:{port}...")
    try:
        from over_ip.discovery import PeerDiscoveryService
        PeerDiscoveryService.get_instance(port=port).start()
    except Exception as e:
        logger.warning(f"[Discovery] Could not start UDP discovery service: {e}")
    app.run(host=host, port=port, debug=debug, threaded=True)
