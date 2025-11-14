"""Caching service with support for in-memory and Redis backends."""

from aiocache import Cache
from aiocache.serializers import JsonSerializer

from app.core.config import settings


def get_cache() -> Cache:
    """
    Returns a cache instance based on environment configuration.

    If REDIS_URL is set, a Redis cache is returned. Otherwise, a simple
    in-memory cache is used.
    """
    if settings.REDIS_URL:
        return Cache(
            Cache.REDIS,
            endpoint=settings.REDIS_URL,
            port=6379,
            namespace="mcp",
            serializer=JsonSerializer(),
        )
    return Cache(Cache.MEMORY, namespace="mcp", serializer=JsonSerializer())


cache = get_cache()
