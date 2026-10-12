import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.db.models import Game, Platform, Store, GameOffer, PriceHistory, SearchCache, GamePlatform


@pytest.mark.asyncio
async def test_create_game(session):
    game = Game(
        id=uuid4(),
        title="Test Game",
        slug="test-game",
        description="A test game",
        release_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
    session.add(game)
    await session.commit()
    await session.refresh(game)

    assert game.id is not None
    assert game.title == "Test Game"
    assert game.slug == "test-game"
    assert game.created_at is not None
    assert game.updated_at is not None


@pytest.mark.asyncio
async def test_game_unique_slug(session):
    game1 = Game(id=uuid4(), title="Game 1", slug="same-slug")
    game2 = Game(id=uuid4(), title="Game 2", slug="same-slug")
    session.add(game1)
    await session.commit()

    session.add(game2)
    with pytest.raises(Exception):
        await session.commit()


@pytest.mark.asyncio
async def test_create_platform(session):
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    session.add(platform)
    await session.commit()
    await session.refresh(platform)

    assert platform.id is not None
    assert platform.name == "PC"
    assert platform.slug == "pc"


@pytest.mark.asyncio
async def test_game_platform_relationship(session):
    game = Game(id=uuid4(), title="Test Game", slug="test-game")
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    session.add_all([game, platform])
    await session.commit()

    gp = GamePlatform(game_id=game.id, platform_id=platform.id)
    session.add(gp)
    await session.commit()

    await session.refresh(game)
    await session.refresh(platform)

    assert platform in game.platforms
    assert game in platform.games


@pytest.mark.asyncio
async def test_create_store(session):
    store = Store(id=uuid4(), name="Steam", slug="steam", base_url="https://store.steampowered.com")
    session.add(store)
    await session.commit()
    await session.refresh(store)

    assert store.id is not None
    assert store.name == "Steam"
    assert store.is_active is True


@pytest.mark.asyncio
async def test_create_game_offer(session):
    game = Game(id=uuid4(), title="Test Game", slug="test-game")
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    store = Store(id=uuid4(), name="Steam", slug="steam")
    session.add_all([game, platform, store])
    await session.commit()

    offer = GameOffer(
        id=uuid4(),
        game_id=game.id,
        store_id=store.id,
        platform_id=platform.id,
        currency="USD",
        current_price=Decimal("29.99"),
        regular_price=Decimal("39.99"),
        is_available=True,
    )
    session.add(offer)
    await session.commit()
    await session.refresh(offer)

    assert offer.id is not None
    assert offer.current_price == Decimal("29.99")
    assert offer.regular_price == Decimal("39.99")


@pytest.mark.asyncio
async def test_offer_unique_constraint(session):
    game = Game(id=uuid4(), title="Test Game", slug="test-game")
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    store = Store(id=uuid4(), name="Steam", slug="steam")
    session.add_all([game, platform, store])
    await session.commit()

    offer1 = GameOffer(
        id=uuid4(), game_id=game.id, store_id=store.id, platform_id=platform.id,
        external_id="same-external-id",
        currency="USD", current_price=Decimal("29.99"), is_available=True,
    )
    offer2 = GameOffer(
        id=uuid4(), game_id=game.id, store_id=store.id, platform_id=platform.id,
        external_id="same-external-id",
        currency="USD", current_price=Decimal("19.99"), is_available=True,
    )
    session.add(offer1)
    await session.commit()

    session.add(offer2)
    with pytest.raises(Exception):
        await session.commit()


@pytest.mark.asyncio
async def test_price_history(session):
    game = Game(id=uuid4(), title="Test Game", slug="test-game")
    platform = Platform(id=uuid4(), name="PC", slug="pc")
    store = Store(id=uuid4(), name="Steam", slug="steam")
    session.add_all([game, platform, store])
    await session.commit()

    offer = GameOffer(
        id=uuid4(), game_id=game.id, store_id=store.id, platform_id=platform.id,
        currency="USD", current_price=Decimal("29.99"), is_available=True,
    )
    session.add(offer)
    await session.commit()

    history = PriceHistory(
        id=uuid4(),
        offer_id=offer.id,
        store_id=store.id,
        price=Decimal("29.99"),
        regular_price=Decimal("39.99"),
        currency="USD",
        availability=True,
    )
    session.add(history)
    await session.commit()
    await session.refresh(history)

    assert history.id is not None
    assert history.price == Decimal("29.99")
    assert history.recorded_at is not None


@pytest.mark.asyncio
async def test_search_cache(session):
    cache = SearchCache(
        id=uuid4(),
        cache_key="test-key",
        query="test query",
        filters={"platform": "pc"},
        result_data={"games": ["game1", "game2"]},
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    session.add(cache)
    await session.commit()
    await session.refresh(cache)

    assert cache.id is not None
    assert cache.cache_key == "test-key"
    assert cache.result_data == {"games": ["game1", "game2"]}