"""
Base Repository class providing cache-awareness and fallback mechanisms.
"""
from typing import Optional, Any, Dict
import config_manager
import redis_cache
from utils import get_logger

logger = get_logger()


class BaseRepository:
    """
    Abstract Base Repository supporting Redis caching when enabled in config.json,
    with automatic in-memory fallback when Redis is disabled or offline.
    """
    _mem_cache: Dict[str, Any] = {}

    def _get_redis_config(self) -> Optional[Dict[str, Any]]:
        """Fetch Redis configuration dictionary from config.json."""
        try:
            cfg = config_manager.load_config()
            return cfg.get("redis")
        except Exception as e:
            logger.error(f"[Repository] Error loading config: {e}")
            return None

    _get_redis_cfg = _get_redis_config

    def _cache_get(self, key: str) -> Optional[Any]:
        """Attempt to retrieve deserialized JSON data from Redis cache, falling back to memory."""
        redis_cfg = self._get_redis_config()
        if redis_cfg and redis_cfg.get("enabled", False):
            try:
                val = redis_cache.get_json(redis_cfg, key)
                if val is not None:
                    return val
            except Exception as e:
                logger.warning(f"[Repository] Redis get error: {e}")
        # In-memory fallback when Redis is disabled, offline, or cache miss
        return BaseRepository._mem_cache.get(key)

    def _cache_set(self, key: str, data: Any, ttl_seconds: Optional[int] = None):
        """Save data to memory fallback and to Redis cache if enabled."""
        BaseRepository._mem_cache[key] = data
        redis_cfg = self._get_redis_config()
        if not redis_cfg or not redis_cfg.get("enabled", False):
            return
        try:
            redis_cache.set_json(redis_cfg, key, data, ttl_seconds)
        except Exception as e:
            logger.warning(f"[Repository] Redis set error: {e}")

    def _cache_delete(self, key: str):
        """Delete a single key from memory and Redis cache."""
        BaseRepository._mem_cache.pop(key, None)
        redis_cfg = self._get_redis_config()
        if not redis_cfg or not redis_cfg.get("enabled", False):
            return
        try:
            redis_cache.delete_cache(redis_cfg, key)
        except Exception as e:
            logger.warning(f"[Repository] Redis delete error: {e}")

    def _cache_delete_pattern(self, pattern: str):
        """Delete keys matching pattern from memory and Redis cache."""
        prefix = pattern.replace("*", "")
        keys_to_del = [k for k in list(BaseRepository._mem_cache.keys()) if k.startswith(prefix)]
        for k in keys_to_del:
            BaseRepository._mem_cache.pop(k, None)
        redis_cfg = self._get_redis_config()
        if not redis_cfg or not redis_cfg.get("enabled", False):
            return
        try:
            redis_cache.delete_cache_pattern(redis_cfg, pattern)
        except Exception as e:
            logger.warning(f"[Repository] Redis delete pattern error: {e}")
