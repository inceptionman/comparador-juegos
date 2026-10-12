import json
from typing import Any, Optional

import redis.asyncio as redis

from app.cache.base import CacheBackend
from app.core.config import get_settings


class RedisCache(CacheBackend):
    def __init__(self):
        self.settings = get_settings()
        self._client: redis.Redis | None = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                self.settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        try:
            client = await self._get_client()
            await client.setex(key, ttl, json.dumps(value))
        except Exception:
            pass  # Silently fail cache operations

    async def delete(self, key: str) -> bool:
        try:
            client = await self._get_client()
            result = await client.delete(key)
            return result > 0
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        try:
            client = await self._get_client()
            return await client.exists(key) > 0
        except Exception:
            return False

    async def cleanup_expired(self) -> int:
        # Redis handles expiration automatically
        return 0

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None