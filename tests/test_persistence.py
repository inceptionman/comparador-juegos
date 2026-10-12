import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.services.persistence import PersistenceService
from app.db.models import Game, Platform, Store, GameOffer, PriceHistory


@pytest.mark.asyncio
async def test_create_or_get_game_new(session):
    service = PersistenceService(session)
    game = await service.create_or_get_game(
        title="New Game",
        slug="new-game",
        external_id="ext-123",
    )
    assert game.title == "New Game"
    assert game.slug == "new-game"
    assert game.external_id == "ext-123"


@pytest.mark.asyncio
async def test_create_or_get_game_existing_by_external_id(session):
    service = PersistenceService(session)
    existing = Game(id=uuid4(), title="Existing", slug="existing", external_id="ext-123")
    session.add(existing)
    await session.commit()

    game = await service.create_or_get_game(
        title="New Game",
        slug="new-game",
        external_id="ext-123",
    )
    assert game.id == existing.id
    assert game.title == "Existing"


@pytest.mark.asyncio
async def test_create_or_get_game_existing_by_slug(session):
    service = PersistenceService(session)
    existing = Game(id=uuid4(), title="Existing", slug="existing-game")
    session.add(existing)
    await session.commit()

    game = await service.create_or_get_game(
        title="New Game",
        slug="existing-game",
    )
    assert game.id == existing.id


@pytest.mark.asyncio
async def test_create_or_get_platform(session):
    service = PersistenceService(session)
    platform = await service.create_or_get_platform("PlayStation 5", "ps5")
    assert platform.name == "PlayStation 5"
    assert platform.slug == "ps5"

    # Second call should return existing
    platform2 = await service.create_or_get_platform("PlayStation 5", "ps5")
    assert platform2.id == platform.id


@pytest.mark.asyncio
async def test_create_or_get_store(session):
    service = PersistenceService(session)
    store = await service.create_or_get_store("Epic Games", "epic", "https://epicgames.com")
    assert store.name == "Epic Games"
    assert store.slug == "epic"
    assert store.base_url == "https://epicgames.com"


@pytest.mark.asyncio
async def test_upsert_offer_creates_new(session):
    service = PersistenceService(session)
    game = Game(id=uuid4(), title="Game", slug="game")
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    store = Store(id=uuid4(), name="Store", slug="store")
    session.add_all([game, platform, store])
    await session.commit()

    offer, recorded = await service.upsert_offer(
        game_id=game.id,
        store_id=store.id,
        platform_id=platform.id,
        external_id=None,
        product_url="https://store.com/game",
        currency="USD",
        current_price=Decimal("29.99"),
        regular_price=Decimal("39.99"),
        is_available=True,
    )
    assert offer.current_price == Decimal("29.99")
    assert recorded is True

    # Check history was created
    histories = await service.price_history.get_by_offer(offer.id)
    assert len(histories) == 1
    assert histories[0].price == Decimal("29.99")


@pytest.mark.asyncio
async def test_upsert_offer_updates_existing(session):
    service = PersistenceService(session)
    game = Game(id=uuid4(), title="Game", slug="game")
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    store = Store(id=uuid4(), name="Store", slug="store")
    session.add_all([game, platform, store])
    await session.commit()

    # Create initial offer
    offer1, _ = await service.upsert_offer(
        game_id=game.id,
        store_id=store.id,
        platform_id=platform.id,
        external_id=None,
        product_url="https://store.com/game",
        currency="USD",
        current_price=Decimal("29.99"),
        regular_price=Decimal("39.99"),
        is_available=True,
    )
    await session.commit()

    # Update price
    offer2, recorded = await service.upsert_offer(
        game_id=game.id,
        store_id=store.id,
        platform_id=platform.id,
        external_id=None,
        product_url="https://store.com/game",
        currency="USD",
        current_price=Decimal("19.99"),
        regular_price=Decimal("29.99"),
        is_available=True,
    )
    assert offer2.id == offer1.id
    assert offer2.current_price == Decimal("19.99")
    assert recorded is True

    # Check history was created
    histories = await service.price_history.get_by_offer(offer1.id)
    assert len(histories) == 2
    # Both history entries should have the old price (29.99) since history records price before change
    prices = {h.price for h in histories}
    assert prices == {Decimal("29.99")}
    # Current offer price should be updated
    assert offer2.current_price == Decimal("19.99")


@pytest.mark.asyncio
async def test_upsert_offer_same_price_no_history(session):
    service = PersistenceService(session)
    game = Game(id=uuid4(), title="Game", slug="game")
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    store = Store(id=uuid4(), name="Store", slug="store")
    session.add_all([game, platform, store])
    await session.commit()

    await service.upsert_offer(
        game_id=game.id,
        store_id=store.id,
        platform_id=platform.id,
        external_id=None,
        product_url=None,
        currency="USD",
        current_price=Decimal("29.99"),
        regular_price=Decimal("39.99"),
        is_available=True,
    )
    await session.commit()

    # Same price - should not record history
    offer, recorded = await service.upsert_offer(
        game_id=game.id,
        store_id=store.id,
        platform_id=platform.id,
        external_id=None,
        product_url=None,
        currency="USD",
        current_price=Decimal("29.99"),
        regular_price=Decimal("39.99"),
        is_available=True,
    )
    assert recorded is False

    histories = await service.price_history.get_by_offer(offer.id)
    assert len(histories) == 1


@pytest.mark.asyncio
async def test_get_game_with_offers(session):
    service = PersistenceService(session)
    game = Game(id=uuid4(), title="Game", slug="game")
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    store = Store(id=uuid4(), name="Store", slug="store")
    session.add_all([game, platform, store])
    await session.commit()

    await service.upsert_offer(
        game_id=game.id,
        store_id=store.id,
        platform_id=platform.id,
        external_id=None,
        product_url=None,
        currency="USD",
        current_price=Decimal("29.99"),
        regular_price=None,
        is_available=True,
    )
    await session.commit()

    game_with_offers = await service.get_game_with_offers(game.id)
    assert game_with_offers is not None
    assert len(game_with_offers.offers) == 1


@pytest.mark.asyncio
async def test_get_price_history(session):
    service = PersistenceService(session)
    game = Game(id=uuid4(), title="Game", slug="game")
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    store = Store(id=uuid4(), name="Store", slug="store")
    session.add_all([game, platform, store])
    await session.commit()

    await service.upsert_offer(
        game_id=game.id,
        store_id=store.id,
        platform_id=platform.id,
        external_id=None,
        product_url=None,
        currency="USD",
        current_price=Decimal("29.99"),
        regular_price=Decimal("39.99"),
        is_available=True,
    )
    await session.commit()

    # Update price
    await service.upsert_offer(
        game_id=game.id,
        store_id=store.id,
        platform_id=platform.id,
        external_id=None,
        product_url=None,
        currency="USD",
        current_price=Decimal("19.99"),
        regular_price=Decimal("29.99"),
        is_available=True,
    )
    await session.commit()

    offer = (await service.offers.get_by_game(game.id))[0]
    history = await service.get_price_history(offer.id)
    assert len(history) == 2
    # Both history entries should have the old price (29.99) since history records price before change
    prices = {h.price for h in history}
    assert prices == {Decimal("29.99")}
    # Current offer price should be updated
    assert offer.current_price == Decimal("19.99")