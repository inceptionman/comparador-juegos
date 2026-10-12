from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Store, GameOffer, PriceHistory
from app.repositories.base import BaseRepository


class StoreRepository(BaseRepository[Store]):
    async def get_by_id(self, id: UUID) -> Store | None:
        stmt = select(Store).where(Store.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Store | None:
        stmt = select(Store).where(Store.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0, active_only: bool = False) -> Sequence[Store]:
        stmt = select(Store).limit(limit).offset(offset).order_by(Store.name)
        if active_only:
            stmt = stmt.where(Store.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: Store) -> Store:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: Store) -> Store:
        obj.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        store = await self.get_by_id(id)
        if store:
            await self.session.delete(store)
            return True
        return False


class GameOfferRepository(BaseRepository[GameOffer]):
    async def get_by_id(self, id: UUID) -> GameOffer | None:
        stmt = (
            select(GameOffer)
            .where(GameOffer.id == id)
            .options(
                selectinload(GameOffer.game),
                selectinload(GameOffer.store),
                selectinload(GameOffer.platform),
                selectinload(GameOffer.price_history),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_game_store_platform(
        self, game_id: UUID, store_id: UUID, platform_id: UUID, external_id: str | None = None
    ) -> GameOffer | None:
        stmt = select(GameOffer).where(
            and_(
                GameOffer.game_id == game_id,
                GameOffer.store_id == store_id,
                GameOffer.platform_id == platform_id,
            )
        )
        if external_id:
            stmt = stmt.where(GameOffer.external_id == external_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_game(self, game_id: UUID) -> Sequence[GameOffer]:
        stmt = (
            select(GameOffer)
            .where(GameOffer.game_id == game_id)
            .options(selectinload(GameOffer.store), selectinload(GameOffer.platform))
            .order_by(GameOffer.current_price)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[GameOffer]:
        stmt = select(GameOffer).limit(limit).offset(offset).order_by(GameOffer.last_checked_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_available_offers(self, game_id: UUID) -> Sequence[GameOffer]:
        stmt = (
            select(GameOffer)
            .where(and_(GameOffer.game_id == game_id, GameOffer.is_available == True))
            .options(selectinload(GameOffer.store), selectinload(GameOffer.platform))
            .order_by(GameOffer.current_price)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: GameOffer) -> GameOffer:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: GameOffer) -> GameOffer:
        obj.updated_at = datetime.now(timezone.utc)
        obj.last_checked_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update_price(
        self,
        offer_id: UUID,
        current_price: str,
        regular_price: str | None,
        currency: str,
        is_available: bool,
    ) -> GameOffer | None:
        offer = await self.get_by_id(offer_id)
        if offer:
            from decimal import Decimal
            offer.current_price = Decimal(current_price)
            if regular_price:
                offer.regular_price = Decimal(regular_price)
            offer.currency = currency
            offer.is_available = is_available
            offer.last_checked_at = datetime.now(timezone.utc)
            offer.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(offer)
        return offer

    async def delete(self, id: UUID) -> bool:
        offer = await self.get_by_id(id)
        if offer:
            await self.session.delete(offer)
            return True
        return False


class PriceHistoryRepository(BaseRepository[PriceHistory]):
    async def get_by_id(self, id: UUID) -> PriceHistory | None:
        stmt = select(PriceHistory).where(PriceHistory.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_offer(
        self, offer_id: UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[PriceHistory]:
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.offer_id == offer_id)
            .order_by(PriceHistory.recorded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_offer_and_date_range(
        self, offer_id: UUID, start_date: datetime, end_date: datetime
    ) -> Sequence[PriceHistory]:
        stmt = (
            select(PriceHistory)
            .where(
                and_(
                    PriceHistory.offer_id == offer_id,
                    PriceHistory.recorded_at >= start_date,
                    PriceHistory.recorded_at <= end_date,
                )
            )
            .order_by(PriceHistory.recorded_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_by_offer(self, offer_id: UUID) -> PriceHistory | None:
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.offer_id == offer_id)
            .order_by(PriceHistory.recorded_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[PriceHistory]:
        stmt = select(PriceHistory).limit(limit).offset(offset).order_by(PriceHistory.recorded_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: PriceHistory) -> PriceHistory:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: PriceHistory) -> PriceHistory:
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        history = await self.get_by_id(id)
        if history:
            await self.session.delete(history)
            return True
        return False

    async def should_record_price(
        self,
        offer_id: UUID,
        price: str,
        currency: str,
        availability: bool,
    ) -> bool:
        latest = await self.get_latest_by_offer(offer_id)
        if not latest:
            return True
        from decimal import Decimal
        return (
            latest.price != Decimal(price)
            or latest.currency != currency
            or latest.availability != availability
        )