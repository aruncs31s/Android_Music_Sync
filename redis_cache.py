"""
Redis caching module for ADB song query results.
Caches device content query outputs in Redis if configured in config.json.
If Redis is enabled in config.json but fails to connect, CRASHES THE APP immediately.
"""
import sys
from typing import Optional, Dict, Any

REDIS_AVAILABLE = False
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


def _get_redis_client(redis_cfg: Optional[Dict[str, Any]]):
    """
    Helper to establish Redis connection if redis-py is installed and enabled in config.
    CRASHES THE APP if redis is enabled but cannot connect.
    """
    if not redis_cfg or not redis_cfg.get("enabled", False):
        return None

    if not REDIS_AVAILABLE:
        raise RuntimeError(
            "CRITICAL: Redis is enabled in config.json, but the 'redis' Python package is not installed!\n"
            "Please install it via: pip install redis"
        )

    host = redis_cfg.get("host", "localhost")
    port = int(redis_cfg.get("port", 8998))
    db = int(redis_cfg.get("db", 0))
    password = redis_cfg.get("password") or None

    try:
        r = redis.Redis(host=host, port=port, db=db, password=password, socket_timeout=3.0)
        # Verify connection
        r.ping()
        return r
    except Exception as e:
        raise RuntimeError(
            f"CRITICAL REDIS ERROR: Redis is enabled in config.json, but failed to connect to Redis server at {host}:{port}!\n"
            f"Error details: {e}\n"
            f"Please verify that Redis server is running on {host}:{port} with password '{password}'."
        )


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
