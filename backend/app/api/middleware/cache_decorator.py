"""
Response caching decorator for FastAPI endpoints.

Caches responses in Redis to avoid duplicate work for identical requests.
"""

from functools import wraps
from typing import Callable, Optional
from fastapi import Request
from app.services.cache_client.redis_client import cache
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def cache_response(ttl: int = 60, key_prefix: str = "api"):
    """
    Decorator to cache API responses in Redis.

    Args:
        ttl: Time to live in seconds (default: 60)
        key_prefix: Prefix for cache key (default: "api")

    Usage:
        @router.get("/endpoint")
        @cache_response(ttl=300, key_prefix="ec2")
        async def my_endpoint(request: Request):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                # If no request object, just call function
                return await func(*args, **kwargs)

            # Build cache key from path, query params, and user
            user_id = "anonymous"
            if hasattr(request.state, 'user_id'):
                user_id = request.state.user_id

            # Create deterministic cache key
            cache_parts = [
                key_prefix,
                request.url.path,
                str(sorted(request.query_params.items())),
                user_id
            ]
            cache_str = ":".join(cache_parts)
            cache_key = f"response:{hashlib.md5(cache_str.encode()).hexdigest()}"

            # Try to get from cache
            try:
                cached = cache.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache HIT: {request.url.path}")
                    return cached
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

            # Cache miss - execute function
            logger.debug(f"Cache MISS: {request.url.path}")
            response = await func(*args, **kwargs)

            # Store in cache
            try:
                cache.set(cache_key, response, ttl=ttl)
            except Exception as e:
                logger.warning(f"Cache write error: {e}")

            return response

        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate all cache keys matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "api:ec2:*")

    Usage:
        invalidate_cache_pattern("api:ec2:*")  # Clear all EC2 caches
    """
    try:
        deleted = cache.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache keys matching: {pattern}")
        return deleted
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return 0
