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
    with automatic fallback to DB / filesystem when Redis is disabled or offline.
    """

    def _get_redis_config(self) -> Optional[Dict[str, Any]]:
        """Fetch Redis configuration dictionary from config.json."""
        try:
            cfg = config_manager.load_config()
            return cfg.get("redis")
        except Exception as e:
            logger.error(f"[Repository] Error loading config: {e}")
            return None

    def _cache_get(self, key: str) -> Optional[Any]:
        """Attempt to retrieve deserialized JSON data from Redis cache."""
        redis_cfg = self._get_redis_config()
        if not redis_cfg or not redis_cfg.get("enabled", False):
            return None
        return redis_cache.get_json(redis_cfg, key)

    def _cache_set(self, key: str, data: Any, ttl_seconds: Optional[int] = None):
        """Attempt to save data to Redis cache as JSON."""
        redis_cfg = self._get_redis_config()
        if not redis_cfg or not redis_cfg.get("enabled", False):
            return
        redis_cache.set_json(redis_cfg, key, data, ttl_seconds)

    def _cache_delete(self, key: str):
        """Delete a single key from Redis cache."""
        redis_cfg = self._get_redis_config()
        if not redis_cfg or not redis_cfg.get("enabled", False):
            return
        redis_cache.delete_cache(redis_cfg, key)

    def _cache_delete_pattern(self, pattern: str):
        """Delete keys matching pattern from Redis cache."""
        redis_cfg = self._get_redis_config()
        if not redis_cfg or not redis_cfg.get("enabled", False):
            return
        redis_cache.delete_cache_pattern(redis_cfg, pattern)
