from typing import Any, Optional
import hashlib

from app.cache.base import CacheBackend
from app.cache.redis_cache import RedisCache
from app.cache.database_cache import DatabaseCache
from app.core.config import get_settings


class CacheService:
    def __init__(self, backend: CacheBackend | None = None):
        self.settings = get_settings()
        self._backend = backend

    @property
    def backend(self) -> CacheBackend:
        if self._backend is None:
            if self.settings.CACHE_ENABLED:
                try:
                    self._backend = RedisCache()
                except Exception:
                    self._backend = None
            if self._backend is None:
                # We'll use database cache lazily when a session is available
                raise RuntimeError("Cache backend not initialized. Use CacheService.with_session() for database cache.")
        return self._backend

    @classmethod
    def with_session(cls, session) -> "CacheService":
        service = cls()
        service._backend = DatabaseCache(session)
        return service

    def _generate_key(self, query: str, filters: dict | None = None) -> str:
        key_data = f"{query}:{filters or {}}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:64]

    async def get(self, query: str, filters: dict | None = None) -> Any | None:
        key = self._generate_key(query, filters)
        return await self.backend.get(key)

    async def set(self, query: str, value: Any, filters: dict | None = None, ttl: int | None = None) -> None:
        key = self._generate_key(query, filters)
        ttl = ttl or self.settings.CACHE_TTL_SECONDS
        await self.backend.set(key, value, ttl)

    async def delete(self, query: str, filters: dict | None = None) -> bool:
        key = self._generate_key(query, filters)
        return await self.backend.delete(key)

    async def invalidate_by_game(self, game_id: str) -> int:
        # This would require a more sophisticated cache key tracking mechanism
        # For now, we just clean up expired entries
        return await self.backend.cleanup_expired()

    async def cleanup_expired(self) -> int:
        return await self.backend.cleanup_expired()

    async def close(self) -> None:
        if self._backend:
            await self._backend.close()