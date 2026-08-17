from __future__ import annotations

from functools import lru_cache

import redis.asyncio as redis

from app.core.config import settings


@lru_cache
def get_redis_client() -> redis.Redis:
    return redis.from_url(
        settings.redis_url,
        socket_timeout=settings.redis_socket_timeout_seconds,
        decode_responses=True,
    )
