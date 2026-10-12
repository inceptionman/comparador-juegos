from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Game, Platform, Store, GameOffer, PriceHistory
from app.repositories import (
    GameRepository,
    PlatformRepository,
    StoreRepository,
    GameOfferRepository,
    PriceHistoryRepository,
    SearchCacheRepository,
)


class PersistenceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.games = GameRepository(session)
        self.platforms = PlatformRepository(session)
        self.stores = StoreRepository(session)
        self.offers = GameOfferRepository(session)
        self.price_history = PriceHistoryRepository(session)
        self.search_cache = SearchCacheRepository(session)

    async def create_or_get_game(
        self,
        title: str,
        slug: str,
        description: str | None = None,
        release_date: datetime | None = None,
        external_id: str | None = None,
    ) -> Game:
        if external_id:
            existing = await self.games.get_by_external_id(external_id)
            if existing:
                return existing

        existing = await self.games.get_by_slug(slug)
        if existing:
            return existing

        game = Game(
            id=uuid4(),
            title=title,
            slug=slug,
            description=description,
            release_date=release_date,
            external_id=external_id,
        )
        return await self.games.create(game)

    async def create_or_get_platform(self, name: str, slug: str) -> Platform:
        existing = await self.platforms.get_by_slug(slug)
        if existing:
            return existing

        platform = Platform(id=uuid4(), name=name, slug=slug)
        return await self.platforms.create(platform)

    async def create_or_get_store(self, name: str, slug: str, base_url: str | None = None) -> Store:
        existing = await self.stores.get_by_slug(slug)
        if existing:
            return existing

        store = Store(id=uuid4(), name=name, slug=slug, base_url=base_url)
        return await self.stores.create(store)

    async def upsert_offer(
        self,
        game_id: UUID,
        store_id: UUID,
        platform_id: UUID,
        external_id: str | None,
        product_url: str | None,
        currency: str,
        current_price: Decimal,
        regular_price: Decimal | None,
        is_available: bool,
    ) -> tuple[GameOffer, bool]:
        existing = await self.offers.get_by_game_store_platform(
            game_id, store_id, platform_id, external_id
        )

        should_record_history = True
        if existing:
            should_record_history = await self.price_history.should_record_price(
                existing.id,
                str(current_price),
                currency,
                is_available,
            )

            if should_record_history:
                history = PriceHistory(
                    id=uuid4(),
                    offer_id=existing.id,
                    store_id=store_id,
                    price=existing.current_price,
                    regular_price=existing.regular_price,
                    currency=existing.currency,
                    availability=existing.is_available,
                    recorded_at=datetime.now(timezone.utc),
                    source="auto",
                )
                await self.price_history.create(history)

            existing.current_price = current_price
            existing.regular_price = regular_price
            existing.currency = currency
            existing.is_available = is_available
            existing.product_url = product_url
            existing.last_checked_at = datetime.now(timezone.utc)
            updated = await self.offers.update(existing)
            return updated, should_record_history

        offer = GameOffer(
            id=uuid4(),
            game_id=game_id,
            store_id=store_id,
            platform_id=platform_id,
            external_id=external_id,
            product_url=product_url,
            currency=currency,
            current_price=current_price,
            regular_price=regular_price,
            is_available=is_available,
        )
        created = await self.offers.create(offer)

        history = PriceHistory(
            id=uuid4(),
            offer_id=created.id,
            store_id=store_id,
            price=current_price,
            regular_price=regular_price,
            currency=currency,
            availability=is_available,
            recorded_at=datetime.now(timezone.utc),
            source="auto",
        )
        await self.price_history.create(history)

        return created, True

    async def get_game_with_offers(self, game_id: UUID) -> Game | None:
        return await self.games.get_by_id(game_id)

    async def get_price_history(self, offer_id: UUID, limit: int = 100) -> Sequence[PriceHistory]:
        return await self.price_history.get_by_offer(offer_id, limit=limit)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()