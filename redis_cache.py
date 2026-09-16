"""
Redis caching module with resilient fallback and repository support.
Caches query outputs, JSON data structures, and local folder file indexes in Redis.
If Redis is disabled in config.json or offline, logs a warning and gracefully returns None for fallback.
"""
import sys
import json
import os
from typing import Optional, Dict, Any, List

REDIS_AVAILABLE = False
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

_WARNED_OFFLINE = False


def _get_redis_client(redis_cfg: Optional[Dict[str, Any]]):
    """
    Helper to establish Redis connection if redis-py is installed and enabled in config.
    Gracefully returns None if disabled or if connection fails.
    """
    global _WARNED_OFFLINE
    if not redis_cfg or not redis_cfg.get("enabled", False):
        return None

    if not REDIS_AVAILABLE:
        if not _WARNED_OFFLINE:
            print("[RedisCache] Warning: Redis is enabled in config.json, but 'redis' package is not installed. Falling back to DB/disk.", file=sys.stderr)
            _WARNED_OFFLINE = True
        return None

    host = redis_cfg.get("host", "localhost")
    port = int(redis_cfg.get("port", 8998))
    db = int(redis_cfg.get("db", 0))
    password = redis_cfg.get("password") or None

    try:
        r = redis.Redis(host=host, port=port, db=db, password=password, socket_timeout=2.0)
        r.ping()
        _WARNED_OFFLINE = False
        return r
    except Exception as e:
        if not _WARNED_OFFLINE:
            print(f"[RedisCache] Warning: Could not connect to Redis at {host}:{port} ({e}). Falling back to DB/disk.", file=sys.stderr)
            _WARNED_OFFLINE = True
        return None


def get_cached_songs(serial: str, redis_cfg: Optional[Dict[str, Any]]) -> Optional[str]:
    """Retrieve cached ADB song query output string from Redis."""
    client = _get_redis_client(redis_cfg)
    if not client:
        return None

    key = f"adb_songs:{serial}"
    try:
        cached_bytes = client.get(key)
        if cached_bytes:
            print(f"[RedisCache] Hit! Retrieved cached songs for device [{serial}] from Redis.", file=sys.stderr)
            return cached_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[RedisCache] Read error: {e}", file=sys.stderr)

    return None


def set_cached_songs(serial: str, raw_output: str, redis_cfg: Optional[Dict[str, Any]]):
    """Cache ADB song query output string in Redis with TTL."""
    client = _get_redis_client(redis_cfg)
    if not client or not raw_output:
        return

    key = f"adb_songs:{serial}"
    ttl = int(redis_cfg.get("ttl_seconds", 3600))

    try:
        client.setex(key, ttl, raw_output)
        print(f"[RedisCache] Saved song query results for [{serial}] in Redis (TTL: {ttl}s).", file=sys.stderr)
    except Exception as e:
        print(f"[RedisCache] Write error: {e}", file=sys.stderr)


def invalidate_cache(serial: str, redis_cfg: Optional[Dict[str, Any]]):
    """Invalidate Redis cache for specified device serial."""
    client = _get_redis_client(redis_cfg)
    if not client:
        return

    key = f"adb_songs:{serial}"
    try:
        client.delete(key)
        print(f"[RedisCache] Cleared cached songs for [{serial}].", file=sys.stderr)
    except Exception as e:
        print(f"[RedisCache] Delete error: {e}", file=sys.stderr)


def get_cached_local_index(local_dir: str, redis_cfg: Optional[Dict[str, Any]]) -> Optional[List[Dict[str, str]]]:
    """Retrieve cached local folder music index from Redis."""
    client = _get_redis_client(redis_cfg)
    if not client:
        return None

    key = f"local_music_index:{os.path.abspath(local_dir)}"
    try:
        cached_bytes = client.get(key)
        if cached_bytes:
            print(f"[RedisCache] Hit! Retrieved cached local file index for '{local_dir}' from Redis.", file=sys.stderr)
            return json.loads(cached_bytes.decode("utf-8"))
    except Exception as e:
        print(f"[RedisCache] Read local index error: {e}", file=sys.stderr)

    return None


def set_cached_local_index(local_dir: str, files_data: List[Dict[str, str]], redis_cfg: Optional[Dict[str, Any]]):
    """Cache local folder music index in Redis."""
    client = _get_redis_client(redis_cfg)
    if not client or not files_data:
        return

    key = f"local_music_index:{os.path.abspath(local_dir)}"
    ttl = int(redis_cfg.get("ttl_seconds", 3600))

    try:
        json_data = json.dumps(files_data)
        client.setex(key, ttl, json_data)
        print(f"[RedisCache] Saved local file index for '{local_dir}' in Redis (TTL: {ttl}s).", file=sys.stderr)
    except Exception as e:
        print(f"[RedisCache] Write local index error: {e}", file=sys.stderr)


def get_cache(redis_cfg: Optional[Dict[str, Any]], key: str) -> Optional[str]:
    """Retrieve raw cached string value from Redis by key."""
    client = _get_redis_client(redis_cfg)
    if not client:
        return None

    try:
        val = client.get(key)
        if val:
            return val.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[RedisCache] get_cache error for '{key}': {e}", file=sys.stderr)
    return None


def set_cache(redis_cfg: Optional[Dict[str, Any]], key: str, value: str, ttl_seconds: Optional[int] = None):
    """Save raw string value in Redis by key with optional TTL."""
    client = _get_redis_client(redis_cfg)
    if not client or not value:
        return

    if ttl_seconds is None:
        ttl_seconds = int(redis_cfg.get("ttl_seconds", 3600))

    try:
        client.setex(key, ttl_seconds, value)
    except Exception as e:
        print(f"[RedisCache] set_cache error for '{key}': {e}", file=sys.stderr)


def get_json(redis_cfg: Optional[Dict[str, Any]], key: str) -> Optional[Any]:
    """Retrieve and deserialise JSON cached data from Redis."""
    raw = get_cache(redis_cfg, key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception as e:
        print(f"[RedisCache] JSON decode error for '{key}': {e}", file=sys.stderr)
        return None


def set_json(redis_cfg: Optional[Dict[str, Any]], key: str, data: Any, ttl_seconds: Optional[int] = None):
    """Serialise and save data as JSON in Redis."""
    if data is None:
        return
    try:
        raw = json.dumps(data)
        set_cache(redis_cfg, key, raw, ttl_seconds)
    except Exception as e:
        print(f"[RedisCache] JSON encode error for '{key}': {e}", file=sys.stderr)


def delete_cache(redis_cfg: Optional[Dict[str, Any]], key: str):
    """Delete a key from Redis cache."""
    client = _get_redis_client(redis_cfg)
    if not client:
        return
    try:
        client.delete(key)
    except Exception as e:
        print(f"[RedisCache] delete_cache error for '{key}': {e}", file=sys.stderr)


def delete_cache_pattern(redis_cfg: Optional[Dict[str, Any]], pattern: str):
    """Delete keys matching pattern from Redis cache."""
    client = _get_redis_client(redis_cfg)
    if not client:
        return
    try:
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
    except Exception as e:
        print(f"[RedisCache] delete_cache_pattern error for '{pattern}': {e}", file=sys.stderr)


