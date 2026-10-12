from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SearchCache
from app.repositories.base import BaseRepository


class SearchCacheRepository(BaseRepository[SearchCache]):
    async def get_by_id(self, id: UUID) -> SearchCache | None:
        stmt = select(SearchCache).where(SearchCache.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_cache_key(self, cache_key: str) -> SearchCache | None:
        stmt = select(SearchCache).where(SearchCache.cache_key == cache_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_valid_cache(self, cache_key: str) -> SearchCache | None:
        stmt = select(SearchCache).where(
            and_(
                SearchCache.cache_key == cache_key,
                SearchCache.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[SearchCache]:
        stmt = select(SearchCache).limit(limit).offset(offset).order_by(SearchCache.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: SearchCache) -> SearchCache:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: SearchCache) -> SearchCache:
        obj.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        cache = await self.get_by_id(id)
        if cache:
            await self.session.delete(cache)
            return True
        return False

    async def delete_by_cache_key(self, cache_key: str) -> bool:
        stmt = delete(SearchCache).where(SearchCache.cache_key == cache_key)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def invalidate_by_game(self, game_id: UUID) -> int:
        """Invalidate all cache entries related to a specific game."""
        # This is a simplified approach - in practice, you'd need to track which cache keys
        # are related to which games, or use a more sophisticated invalidation strategy
        stmt = delete(SearchCache)
        result = await self.session.execute(stmt)
        return result.rowcount

    async def cleanup_expired(self) -> int:
        stmt = delete(SearchCache).where(SearchCache.expires_at <= datetime.now(timezone.utc))
        result = await self.session.execute(stmt)
        return result.rowcount