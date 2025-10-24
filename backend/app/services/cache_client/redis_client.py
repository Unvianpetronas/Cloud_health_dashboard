import redis
import json
import logging
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisCache, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return

        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis.ping()
            logger.info("Redis connection successful")
            self.initialized = True
        except redis.ConnectionError as e:
            logger.warning(f"Redis not available: {e}. Caching disabled.")
            self.redis = None
            self.initialized = True

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache_client"""
        if not self.redis:
            return None

        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 60):
        """Set value in cache_client with TTL (seconds)"""
        if not self.redis:
            return False

        try:
            self.redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def delete(self, key: str):
        """Delete key from cache_client"""
        if not self.redis:
            return False

        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.redis:
            return False

        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis CLEAR error: {e}")
            return False


# Global cache_client instance
cache = RedisCache()