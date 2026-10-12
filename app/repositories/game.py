from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Game, Platform, GamePlatform
from app.repositories.base import BaseRepository


class GameRepository(BaseRepository[Game]):
    async def get_by_id(self, id: UUID) -> Game | None:
        stmt = (
            select(Game)
            .where(Game.id == id)
            .options(selectinload(Game.platforms), selectinload(Game.offers))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Game | None:
        stmt = select(Game).where(Game.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Game | None:
        stmt = select(Game).where(Game.external_id == external_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[Game]:
        stmt = select(Game).limit(limit).offset(offset).order_by(Game.title)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_by_title(self, query: str, limit: int = 20) -> Sequence[Game]:
        stmt = (
            select(Game)
            .where(Game.title.ilike(f"%{query}%"))
            .limit(limit)
            .order_by(Game.title)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_platform(self, platform_id: UUID, limit: int = 100, offset: int = 0) -> Sequence[Game]:
        stmt = (
            select(Game)
            .join(GamePlatform)
            .where(GamePlatform.platform_id == platform_id)
            .limit(limit)
            .offset(offset)
            .order_by(Game.title)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: Game) -> Game:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: Game) -> Game:
        obj.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        game = await self.get_by_id(id)
        if game:
            await self.session.delete(game)
            return True
        return False


class PlatformRepository(BaseRepository[Platform]):
    async def get_by_id(self, id: UUID) -> Platform | None:
        stmt = select(Platform).where(Platform.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Platform | None:
        stmt = select(Platform).where(Platform.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[Platform]:
        stmt = select(Platform).limit(limit).offset(offset).order_by(Platform.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: Platform) -> Platform:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: Platform) -> Platform:
        obj.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        platform = await self.get_by_id(id)
        if platform:
            await self.session.delete(platform)
            return True
        return False

    async def add_game_platform(self, game_id: UUID, platform_id: UUID) -> GamePlatform:
        gp = GamePlatform(game_id=game_id, platform_id=platform_id)
        self.session.add(gp)
        await self.session.flush()
        return gp

    async def remove_game_platform(self, game_id: UUID, platform_id: UUID) -> bool:
        stmt = select(GamePlatform).where(
            and_(GamePlatform.game_id == game_id, GamePlatform.platform_id == platform_id)
        )
        result = await self.session.execute(stmt)
        gp = result.scalar_one_or_none()
        if gp:
            await self.session.delete(gp)
            return True
        return False