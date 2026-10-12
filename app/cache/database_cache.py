from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.base import CacheBackend
from app.db.models import SearchCache
from app.core.config import get_settings


class DatabaseCache(CacheBackend):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    def _generate_cache_key(self, query: str, filters: dict | None = None) -> str:
        import hashlib
        key_data = f"{query}:{filters or {}}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:64]

    async def get(self, key: str) -> Any | None:
        stmt = select(SearchCache).where(
            and_(
                SearchCache.cache_key == key,
                SearchCache.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self.session.execute(stmt)
        cache = result.scalar_one_or_none()
        if cache:
            return cache.result_data
        return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        expires_at = datetime.now(timezone.utc)
        from datetime import timedelta
        expires_at = expires_at + timedelta(seconds=ttl)

        existing = await self.get(key)
        if existing is not None:
            stmt = select(SearchCache).where(SearchCache.cache_key == key)
            result = await self.session.execute(stmt)
            cache = result.scalar_one_or_none()
            if cache:
                cache.result_data = value
                cache.expires_at = expires_at
                cache.updated_at = datetime.now(timezone.utc)
        else:
            cache = SearchCache(
                cache_key=key,
                query="",  # We don't store the original query in this implementation
                filters=None,
                result_data=value,
                expires_at=expires_at,
            )
            self.session.add(cache)
        await self.session.flush()

    async def delete(self, key: str) -> bool:
        stmt = delete(SearchCache).where(SearchCache.cache_key == key)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def exists(self, key: str) -> bool:
        stmt = select(SearchCache).where(
            and_(
                SearchCache.cache_key == key,
                SearchCache.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def cleanup_expired(self) -> int:
        stmt = delete(SearchCache).where(SearchCache.expires_at <= datetime.now(timezone.utc))
        result = await self.session.execute(stmt)
        return result.rowcount

    async def close(self) -> None:
        pass  # Session is managed externally