"""
Flask Web Interface & Dashboard REST API Server.
Serves dashboard webpage from ui/templates/ and ui/static/,
using ui/db.db SQLite database for storing dashboard states and hide list.
"""
import os
import sys
import json
import socket
from typing import Dict, Any
from flask import Flask, jsonify, request, send_file, render_template

import config_manager
import over_ip.song_scanner as song_scanner
import ui.db_manager as ui_db
import ui.stats_manager as ui_stats
import hide_list_db
import syncer
import adb_pusher
import sync_checker
from repositories import song_repo, playlist_repo, hide_repo, device_repo, deleted_repo

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


@app.route("/api/songs", methods=["GET"])
def get_songs():
    """Acquire local music library songs sorted by mtime."""
    songs = song_repo.get_all_songs()
    return jsonify(songs)


@app.route("/api/duplicates", methods=["GET"])
def get_duplicates():
    """Return duplicate song clusters."""
    dups = song_repo.get_duplicates()
    return jsonify(dups)


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


@app.route("/api/devices/scan-adb", methods=["POST"])
def scan_adb_devices():
    """Trigger live ADB device discovery scan."""
    adb_devs = ui_stats.scan_adb_devices_info()
    return jsonify({"status": "success", "devices": adb_devs})


@app.route("/api/devices/scan-ip", methods=["POST"])
def scan_ip_hosts():
    """Trigger live ping scan of stored Over-IP peer hosts."""
    ip_devs = ui_stats.scan_over_ip_hosts_info()
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
        print(f"[Web Sync] Error comparing files with device: {e}", file=sys.stderr)
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

    print(f"[Web Sync] Preview for [{serial}]: {len(local_files)} local, "
          f"{len(already_serializable)} already present, {len(to_sync)} to sync.", file=sys.stderr)

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
    Push a list of local filepaths to a target ADB device.
    Records pushes in synced history, triggers media scanner, evicts Redis cache.
    """
    data = request.get_json(silent=True) or {}
    serial = data.get("serial", "").strip()
    file_paths = data.get("files") or []
    remote_dir = data.get("remote_dir") or ""

    if not serial:
        return jsonify({"error": "Missing serial parameter"}), 400
    if not file_paths or not isinstance(file_paths, list):
        return jsonify({"error": "No files selected to sync"}), 400

    cfg = config_manager.load_config()
    if not remote_dir:
        remote_dir = cfg.get("remote_adb_folder", "/storage/emulated/0/Music/ADB")
    redis_cfg = cfg.get("redis")

    results = []
    success_count = 0
    failed_count = 0

    for fp in file_paths:
        fp = os.path.abspath(fp)
        try:
            ok = adb_pusher.push_song_to_device(serial, fp, remote_dir, redis_cfg=redis_cfg)
        except Exception as e:
            ok = False
            result_entry = {"filepath": fp, "success": False, "error": str(e)}
        else:
            result_entry = {"filepath": fp, "success": ok, "error": "" if ok else "ADB push failed"}

        if ok:
            success_count += 1
        else:
            failed_count += 1
        results.append(result_entry)

    print(f"[Web Sync] Pushed {success_count}/{len(file_paths)} files to [{serial}] ({remote_dir}).", file=sys.stderr)

    return jsonify({
        "status": "success",
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
    """
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath", "").strip()
    device_id = data.get("device_id", "").strip()
    remote_dir = data.get("remote_dir") or None
    force = bool(data.get("force", False))

    if not filepath or not device_id:
        return jsonify({"error": "Missing filepath or device_id parameter"}), 400

    result = device_repo.push_song_to_device(
        device_id=device_id,
        local_filepath=filepath,
        remote_dir=remote_dir,
        force=force
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
    file_path = data.get("filepath")
    device_id = data.get("device_id") or "local"
    song_id = data.get("song_id")
    filename = data.get("filename")

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
    """Download/stream audio file specified by filepath or file parameter."""
    file_path = request.args.get("filepath") or request.args.get("file")
    if not file_path:
        return jsonify({"error": "Missing filepath parameter"}), 400

    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        return jsonify({"error": f"File not found: {file_path}"}), 404

    return send_file(file_path, as_attachment=False)


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



def start_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Start Flask Web Dashboard server."""
    print(f"[Web UI Dashboard] Launching web interface on http://{host}:{port}...", flush=True)
    app.run(host=host, port=port, debug=debug, threaded=True)
