"""
HTTP Client Helper for Over-IP Synchronization.
Handles pinging remote hosts, acquiring available songs, downloading songs via HTTP,
and caching IP online statuses with Redis.
"""
import os
import sys
import json
import requests
from typing import List, Dict, Any, Optional

import over_ip.db as ip_db
import redis_cache


def get_base_url(ip_address: str, port: int = 5000) -> str:
    """Format HTTP base URL for an IP and port."""
    ip_clean = ip_address.strip()
    if ip_clean.startswith("http://") or ip_clean.startswith("https://"):
        return ip_clean.rstrip("/")
    return f"http://{ip_clean}:{port}"


def ping_host(
    ip_address: str,
    port: int = 5000,
    timeout: float = 2.5,
    redis_cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Ping a remote host at http://<ip>:<port>/api/ping.
    Updates SQLite DB status and caches online status in Redis.
    """
    base_url = get_base_url(ip_address, port)
    cache_key = f"ip_online:{ip_address}:{port}"

    # Check Redis cache first if configured
    if redis_cfg:
        cached_status = redis_cache.get_cache(redis_cfg, cache_key)
        if cached_status is not None:
            try:
                data = json.loads(cached_status)
                return data
            except Exception:
                pass

    result = {
        "ip": ip_address,
        "port": port,
        "online": False,
        "hostname": "Unknown",
        "song_count": 0,
        "error": None
    }

    try:
        resp = requests.get(f"{base_url}/api/ping", timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            result["online"] = True
            result["hostname"] = data.get("hostname", "Unknown")
            result["song_count"] = data.get("song_count", 0)
            ip_db.update_ip_status(ip_address, is_online=True)
        else:
            result["error"] = f"HTTP {resp.status_code}"
            ip_db.update_ip_status(ip_address, is_online=False)
    except Exception as e:
        result["error"] = str(e)
        ip_db.update_ip_status(ip_address, is_online=False)

    # Store ping result in Redis with a short TTL (e.g. 60 seconds)
    if redis_cfg:
        try:
            redis_cache.set_cache(redis_cfg, cache_key, json.dumps(result), ttl_seconds=60)
        except Exception:
            pass

    return result


def get_remote_songs(
    ip_address: str,
    port: int = 5000,
    redis_cfg: Optional[Dict[str, Any]] = None,
    refresh: bool = False,
    timeout: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Acquire available songs from remote peer over HTTP.
    Songs are returned sorted by modified time (mtime descending).
    """
    base_url = get_base_url(ip_address, port)
    cache_key = f"ip_songs:{ip_address}:{port}"

    if not refresh and redis_cfg:
        cached_str = redis_cache.get_cache(redis_cfg, cache_key)
        if cached_str:
            try:
                return json.loads(cached_str)
            except Exception:
                pass

    url = f"{base_url}/api/songs"
    if refresh:
        url += "?refresh=true"

    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            songs = resp.json()
            if redis_cfg and isinstance(songs, list):
                redis_cache.set_cache(redis_cfg, cache_key, json.dumps(songs))
            return songs
        else:
            print(f"[Over-IP Client] Failed to fetch songs from {ip_address}: HTTP {resp.status_code}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"[Over-IP Client] Error connecting to {ip_address}: {e}", file=sys.stderr)
        return []


def download_remote_song(
    ip_address: str,
    remote_filepath: str,
    dest_filepath: str,
    port: int = 5000,
    timeout: float = 15.0
) -> bool:
    """
    Download an audio file from remote peer over HTTP streaming endpoint.
    """
    base_url = get_base_url(ip_address, port)
    url = f"{base_url}/api/song/stream"

    os.makedirs(os.path.dirname(os.path.abspath(dest_filepath)), exist_ok=True)

    try:
        resp = requests.get(url, params={"filepath": remote_filepath}, stream=True, timeout=timeout)
        if resp.status_code == 200:
            with open(dest_filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            print(f"[Over-IP Download] Successfully downloaded: {os.path.basename(dest_filepath)}", file=sys.stderr)
            return True
        else:
            print(f"[Over-IP Download] HTTP Error {resp.status_code} downloading {remote_filepath}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"[Over-IP Download] Error downloading file over HTTP: {e}", file=sys.stderr)
        return False


def upload_song_to_peer(
    ip_address: str,
    local_filepath: str,
    port: int = 5000,
    timeout: float = 30.0
) -> bool:
    """
    Upload a local audio file to remote peer over HTTP POST endpoint.
    """
    if not os.path.exists(local_filepath):
        print(f"[Over-IP Upload] Local file does not exist: {local_filepath}", file=sys.stderr)
        return False

    base_url = get_base_url(ip_address, port)
    url = f"{base_url}/api/song/upload"

    try:
        with open(local_filepath, "rb") as f:
            files = {"file": (os.path.basename(local_filepath), f)}
            resp = requests.post(url, files=files, timeout=timeout)

        if resp.status_code == 200:
            print(f"[Over-IP Upload] Successfully uploaded: {os.path.basename(local_filepath)}", file=sys.stderr)
            return True
        else:
            print(f"[Over-IP Upload] HTTP Error {resp.status_code} uploading file", file=sys.stderr)
            return False
    except Exception as e:
        print(f"[Over-IP Upload] Error uploading file over HTTP: {e}", file=sys.stderr)
        return False
