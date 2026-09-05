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
    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])
    songs = song_scanner.scan_songs_from_paths(folders, audio_exts)
    return jsonify(songs)


@app.route("/api/duplicates", methods=["GET"])
def get_duplicates():
    """Return duplicate song clusters."""
    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])
    songs = song_scanner.scan_songs_from_paths(folders, audio_exts)
    dups = ui_stats.detect_duplicate_songs(songs)
    return jsonify(dups)


@app.route("/api/hidden", methods=["GET"])
def get_hidden():
    """Return hidden files from ui/db.db."""
    records = ui_db.get_all_hidden_records()
    return jsonify(records)


@app.route("/api/synced", methods=["GET"])
def get_synced():
    """Return synced tracks history from ui/db.db."""
    records = ui_db.get_all_synced_records()
    return jsonify(records)


@app.route("/api/unhide", methods=["POST"])
def unhide_file():
    """Unhide a file path in ui/db.db and sync_hide_list.db."""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath")
    if not filepath:
        return jsonify({"error": "Missing filepath parameter"}), 400

    ui_db.remove_hidden_file(filepath)
    hide_list_db.remove_hidden_file(filepath)
    return jsonify({"status": "success", "message": f"Unhid {filepath}"})


@app.route("/api/hide", methods=["POST"])
def hide_file():
    """Hide a file path in ui/db.db and sync_hide_list.db."""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath")
    if not filepath:
        return jsonify({"error": "Missing filepath parameter"}), 400

    filename = os.path.basename(filepath)
    ui_db.add_hidden_file(filepath, filename)
    hide_list_db.add_hidden_file(filepath, filename)
    return jsonify({"status": "success", "message": f"Hid {filepath}"})


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Return list of all available devices (Local, ADB, Over-IP)."""
    devices = ui_stats.get_all_available_devices()
    return jsonify(devices)


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


@app.route("/api/devices/add-ip", methods=["POST"])
def add_ip_host():
    """Add a new Over-IP peer host address to ui/db.db and ping it."""
    data = request.get_json(silent=True) or {}
    ip_addr = data.get("ip_address") or data.get("ip")
    port = int(data.get("port", 5000))
    alias = data.get("alias", "")

    if not ip_addr:
        return jsonify({"error": "Missing ip_address parameter"}), 400

    conn = ui_db.get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO ip_hosts (ip_address, port, alias, last_seen)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(ip_address) DO UPDATE SET
                port = excluded.port,
                alias = CASE WHEN excluded.alias != '' THEN excluded.alias ELSE ip_hosts.alias END,
                last_seen = CURRENT_TIMESTAMP
            """,
            (ip_addr.strip(), port, alias)
        )

    # Ping immediately
    cfg = config_manager.load_config()
    redis_cfg = cfg.get("redis")
    ping_res = ip_stats_res = ui_stats.scan_over_ip_hosts_info()

    return jsonify({
        "status": "success",
        "message": f"Added Over-IP peer host {ip_addr}:{port}",
        "devices": ip_stats_res
    })


@app.route("/api/song/delete", methods=["POST"])
def delete_song():
    """
    Safely delete local audio file specified by filepath.
    Removes file from disk and cleans up database references.
    """
    data = request.get_json(silent=True) or {}
    file_path = data.get("filepath")
    if not file_path:
        return jsonify({"error": "Missing filepath parameter"}), 400

    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return jsonify({"error": f"File does not exist: {abs_path}"}), 404

    try:
        os.remove(abs_path)
        # Clean up database references
        ui_db.remove_hidden_file(abs_path)
        hide_list_db.remove_hidden_file(abs_path)
        
        # Clear in-memory metadata cache
        audio_metadata.METADATA_CACHE.pop(abs_path, None)

        # Clear Redis cache if active
        cfg = config_manager.load_config()
        redis_cfg = cfg.get("redis")
        if redis_cfg:
            try:
                import redis_cache
                redis_cache.set_cache(redis_cfg, f"over_ip_songs:{socket.gethostname()}", "")
            except Exception:
                pass

        print(f"[Web UI] Deleted file from disk: {abs_path}", file=sys.stderr)
        return jsonify({"status": "success", "message": f"Successfully deleted {os.path.basename(abs_path)}"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete file: {e}"}), 500


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


def start_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Start Flask Web Dashboard server."""
    print(f"[Web UI Dashboard] Launching web interface on http://{host}:{port}...", flush=True)
    app.run(host=host, port=port, debug=debug)
