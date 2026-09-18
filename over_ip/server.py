"""
Flask REST API Server for Over-IP HTTP Synchronization.
Exposes endpoints for ping/health check, available songs list (sorted by mtime),
song file streaming/download, and song upload.
"""
import os
import json
import socket
import sys
import datetime
from typing import Dict, Any
from flask import Flask, jsonify, request, send_file, Response
from werkzeug.utils import secure_filename

import config_manager
import over_ip.song_scanner as song_scanner
import redis_cache
from utils import get_logger
logger = get_logger()

app = Flask(__name__)


def get_server_hostname() -> str:
    """Get local system hostname."""
    try:
        return socket.gethostname()
    except Exception:
        return "UnknownHost"


@app.route("/api/ping", methods=["GET"])
def ping():
    """Heartbeat endpoint for peer online status verification."""
    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])
    songs = song_scanner.scan_songs_from_paths(folders, audio_exts)

    return jsonify({
        "status": "ok",
        "hostname": get_server_hostname(),
        "song_count": len(songs),
        "folders": folders,
        "server_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/api/songs", methods=["GET"])
def get_songs():
    """
    Acquire available songs from all configured local music paths.
    Songs are sorted by file modification timestamp (mtime descending / newest first).
    Uses Redis cache if enabled in config.json.
    """
    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    audio_exts = cfg.get("audio_extensions", [".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"])
    redis_cfg = cfg.get("redis")
    refresh = request.args.get("refresh", "").lower() in ("1", "true", "yes")

    cache_key = f"over_ip_songs:{get_server_hostname()}"

    if not refresh and redis_cfg:
        cached_str = redis_cache.get_cache(redis_cfg, cache_key)
        if cached_str:
            try:
                cached_songs = json.loads(cached_str)
                return jsonify(cached_songs)
            except Exception:
                pass

    songs = song_scanner.scan_songs_from_paths(folders, audio_exts)

    if redis_cfg:
        try:
            redis_cache.set_cache(redis_cfg, cache_key, json.dumps(songs))
        except Exception:
            pass

    return jsonify(songs)


@app.route("/api/song/stream", methods=["GET"])
def stream_song():
    """
    Download/stream audio file specified by filepath or file query parameter.
    """
    file_path = request.args.get("filepath") or request.args.get("file")
    if not file_path:
        return jsonify({"error": "Missing filepath parameter"}), 400

    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        return jsonify({"error": f"File not found: {file_path}"}), 404

    # Send file for streaming / download
    filename = os.path.basename(file_path)
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )


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
    target_folder = folders[0] if folders else "/home/aruncs/Music"

    os.makedirs(target_folder, exist_ok=True)
    dest_path = os.path.join(target_folder, uploaded_file.filename)

    uploaded_file.save(dest_path)

    return jsonify({
        "status": "success",
        "message": f"Saved {uploaded_file.filename}",
        "dest_path": dest_path
    })


@app.route("/api/song/delete", methods=["POST"])
def delete_song():
    """Delete a song file from local music folders via Over-IP HTTP API."""
    data = request.get_json(silent=True) or {}
    file_path = data.get("filepath")
    if not file_path:
        return jsonify({"error": "Missing filepath parameter"}), 400

    cfg = config_manager.load_config()
    folders = config_manager.get_local_sync_folders(cfg)
    abs_path = os.path.abspath(file_path)

    # Security check: must reside in configured music folders or exist
    is_valid = any(abs_path.startswith(os.path.abspath(f)) for f in folders)
    if not is_valid and not os.path.isfile(abs_path):
        return jsonify({"error": f"File '{file_path}' not found in sync folders"}), 404

    try:
        if os.path.isfile(abs_path):
            os.remove(abs_path)
            redis_cfg = cfg.get("redis")
            if redis_cfg:
                redis_cache.delete_cache(redis_cfg, f"over_ip_songs:{get_server_hostname()}")
            return jsonify({
                "status": "success",
                "message": f"Deleted '{os.path.basename(abs_path)}' on host {get_server_hostname()}."
            })
        else:
            return jsonify({"error": f"File '{abs_path}' does not exist"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete file: {e}"}), 500


def start_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Start the Flask API server."""
    logger.info(f"[Over-IP Server] Starting Flask API server on http://{host}:{port}...")
    app.run(host=host, port=port, debug=debug)

