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

import utils.config_manager as config_manager
import over_ip.song_scanner as song_scanner
import database.redis_cache as redis_cache
from utils import get_logger
import uuid
import over_ip.session_state as session_state
import over_ip.session_sse as session_sse
from flask import stream_with_context

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


@app.route("/api/playlists", methods=["GET"])
def get_playlists():
    """List all playlists for Over-IP sync."""
    try:
        from repositories import playlist_repo
        playlists = playlist_repo.get_all_playlists()
        result = []
        for p in playlists:
            if hasattr(p, "to_dict"):
                result.append(p.to_dict())
            elif isinstance(p, dict):
                result.append(p)
            else:
                result.append({
                    "id": getattr(p, "id", 0),
                    "name": getattr(p, "name", ""),
                    "track_count": getattr(p, "track_count", 0),
                    "created_at": getattr(p, "created_at", "")
                })
        return jsonify(result)
    except Exception as e:
        logger.error(f"[OverIP Server] Error fetching playlists: {e}")
        return jsonify([])


@app.route("/api/playlist/tracks", methods=["GET"])
def get_playlist_tracks():
    """List tracks belonging to a playlist by ID or name."""
    try:
        from repositories import playlist_repo
        playlist_id_param = request.args.get("id")
        playlist_name_param = request.args.get("name")

        playlist_id = None
        if playlist_id_param and playlist_id_param.isdigit():
            playlist_id = int(playlist_id_param)
        elif playlist_name_param:
            playlists = playlist_repo.get_all_playlists()
            for p in playlists:
                p_name = getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else "")
                if p_name.lower() == playlist_name_param.lower():
                    playlist_id = getattr(p, "id", None) or (p.get("id") if isinstance(p, dict) else None)
                    break

        if playlist_id is None:
            return jsonify({"error": "Playlist not found"}), 404

        tracks = playlist_repo.get_playlist_tracks(playlist_id)
        result = []
        for t in tracks:
            if hasattr(t, "to_dict"):
                result.append(t.to_dict())
            elif isinstance(t, dict):
                result.append(t)
            else:
                result.append({
                    "id": getattr(t, "id", 0),
                    "playlist_id": getattr(t, "playlist_id", playlist_id),
                    "filepath": getattr(t, "filepath", ""),
                    "filename": getattr(t, "filename", ""),
                    "title": getattr(t, "title", ""),
                    "artist": getattr(t, "artist", ""),
                    "status": getattr(t, "status", "present")
                })
        return jsonify(result)
    except Exception as e:
        logger.error(f"[OverIP Server] Error fetching playlist tracks: {e}")
        return jsonify([])


@app.route("/api/song/stream", methods=["GET"])
def stream_song():
    """
    Download/stream audio file specified by filepath or file query parameter.
    Supports optional target_bitrate query param for on-the-fly quality downconversion.
    """
    file_path = request.args.get("filepath") or request.args.get("file")
    if not file_path:
        return jsonify({"error": "Missing filepath parameter"}), 400

    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        return jsonify({"error": f"File not found: {file_path}"}), 404

    target_bitrate = request.args.get("target_bitrate")
    if target_bitrate and target_bitrate.isdigit():
        target_br = int(target_bitrate)
        try:
            from services.audio_transcoder import AudioTranscoder
            if AudioTranscoder.needs_downconversion(file_path, target_br):
                res = AudioTranscoder.transcode_audio(file_path, target_br)
                if res.success and os.path.isfile(res.output_path):
                    return send_file(
                        res.output_path,
                        as_attachment=True,
                        download_name=os.path.basename(res.output_path)
                    )
        except Exception as e:
            logger.warning(f"[OverIP Server] Transcoding note ({e}), serving original file")

    # Send original file for streaming / download
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


@app.route("/api/session/state", methods=["GET"])
def get_session_state():
    """Return current desktop player state for remote session discovery."""
    state = session_state.get_state()
    # If browser hasn't sent a heartbeat in 15s, mark as not playing
    if session_state.is_stale():
        state["is_playing"] = False
    return jsonify(state)


@app.route("/api/session/heartbeat", methods=["POST"])
def session_heartbeat():
    """Browser sends this every 3 seconds with current player state."""
    data = request.get_json(silent=True) or {}
    session_state.update_state(
        is_playing=data.get("is_playing", False),
        current_title=data.get("current_title", ""),
        current_artist=data.get("current_artist", ""),
        current_filepath=data.get("current_filepath", ""),
        position_ms=int(data.get("position_ms", 0)),
        duration_ms=int(data.get("duration_ms", 0)),
        queue_size=int(data.get("queue_size", 0)),
        repeat_mode=data.get("repeat_mode", "off"),
        is_shuffled=bool(data.get("is_shuffled", False)),
    )
    return jsonify({"ok": True})


@app.route("/api/session/events")
def session_events():
    """SSE endpoint — browser subscribes here to receive remote playback commands."""
    client_id = request.args.get("client_id") or str(uuid.uuid4())
    return Response(
        stream_with_context(session_sse.sse_stream(client_id)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _push_session_command(cmd: str, params: dict = None):
    """Helper to push a session command SSE event and return JSON response."""
    session_sse.push_event("session_command", {"cmd": cmd, **(params or {})})
    return jsonify({"ok": True, "cmd": cmd})


@app.route("/api/session/play", methods=["POST"])
def session_play():
    """Remote: tell desktop browser player to play/resume."""
    return _push_session_command("play")


@app.route("/api/session/pause", methods=["POST"])
def session_pause():
    """Remote: tell desktop browser player to pause."""
    return _push_session_command("pause")


@app.route("/api/session/next", methods=["POST"])
def session_next():
    """Remote: tell desktop browser player to skip to next track."""
    return _push_session_command("next")


@app.route("/api/session/prev", methods=["POST"])
def session_prev():
    """Remote: tell desktop browser player to go to previous track."""
    return _push_session_command("prev")


@app.route("/api/session/seek", methods=["POST"])
def session_seek():
    """Remote: tell desktop browser player to seek to a position."""
    data = request.get_json(silent=True) or {}
    pos_ms = int(request.args.get("position_ms", data.get("position_ms", 0)))
    return _push_session_command("seek", {"position_ms": pos_ms})


@app.route("/api/session/transfer", methods=["POST"])
def session_transfer():
    """Remote: transfer playback to desktop — play a specific song at a given position."""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath", "")
    if not filepath:
        return jsonify({"error": "Missing filepath"}), 400
    title = data.get("title", "")
    artist = data.get("artist", "")
    pos_ms = int(data.get("position_ms", 0))
    stream_url = data.get("stream_url", "")
    return _push_session_command("transfer", {
        "filepath": filepath,
        "title": title,
        "artist": artist,
        "position_ms": pos_ms,
        "stream_url": stream_url,
    })


@app.route("/api/session/queue_inject", methods=["POST"])
def session_queue_inject():
    """Remote: inject a song into the desktop queue."""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath", "")
    if not filepath:
        return jsonify({"error": "Missing filepath"}), 400
    return _push_session_command("queue_inject", {
        "filepath": filepath,
        "title": data.get("title", ""),
        "artist": data.get("artist", ""),
        "stream_url": data.get("stream_url", ""),
    })


def start_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Start the Flask API server."""
    logger.info(f"[Over-IP Server] Starting Flask API server on http://{host}:{port}...")
    app.run(host=host, port=port, debug=debug)

