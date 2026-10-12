import pytest
import pytest_asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.repositories import (
    GameRepository,
    PlatformRepository,
    StoreRepository,
    GameOfferRepository,
    PriceHistoryRepository,
    SearchCacheRepository,
)
from app.db.models import Game, Platform, Store, GameOffer, PriceHistory, SearchCache


@pytest_asyncio.fixture
async def sample_data(session):
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
        is_available=True,
    )
    session.add(offer)
    await session.commit()

    return {"game": game, "platform": platform, "store": store, "offer": offer}


@pytest.mark.asyncio
async def test_game_repository_get_by_id(session, sample_data):
    repo = GameRepository(session)
    game = await repo.get_by_id(sample_data["game"].id)
    assert game is not None
    assert game.title == "Test Game"


@pytest.mark.asyncio
async def test_game_repository_get_by_slug(session, sample_data):
    repo = GameRepository(session)
    game = await repo.get_by_slug("test-game")
    assert game is not None
    assert game.id == sample_data["game"].id


@pytest.mark.asyncio
async def test_game_repository_search_by_title(session, sample_data):
    repo = GameRepository(session)
    games = await repo.search_by_title("Test")
    assert len(games) == 1
    assert games[0].title == "Test Game"


@pytest.mark.asyncio
async def test_platform_repository_get_by_slug(session, sample_data):
    repo = PlatformRepository(session)
    platform = await repo.get_by_slug("pc")
    assert platform is not None
    assert platform.id == sample_data["platform"].id


@pytest.mark.asyncio
async def test_store_repository_get_by_slug(session, sample_data):
    repo = StoreRepository(session)
    store = await repo.get_by_slug("steam")
    assert store is not None
    assert store.id == sample_data["store"].id


@pytest.mark.asyncio
async def test_store_repository_active_only(session):
    store1 = Store(id=uuid4(), name="Active Store", slug="active", is_active=True)
    store2 = Store(id=uuid4(), name="Inactive Store", slug="inactive", is_active=False)
    session.add_all([store1, store2])
    await session.commit()

    repo = StoreRepository(session)
    active_stores = await repo.get_all(active_only=True)
    assert len(active_stores) == 1
    assert active_stores[0].slug == "active"


@pytest.mark.asyncio
async def test_game_offer_repository_get_by_id(session, sample_data):
    repo = GameOfferRepository(session)
    offer = await repo.get_by_id(sample_data["offer"].id)
    assert offer is not None
    assert offer.current_price == Decimal("29.99")


@pytest.mark.asyncio
async def test_game_offer_repository_get_by_game(session, sample_data):
    repo = GameOfferRepository(session)
    offers = await repo.get_by_game(sample_data["game"].id)
    assert len(offers) == 1
    assert offers[0].id == sample_data["offer"].id


@pytest.mark.asyncio
async def test_game_offer_repository_get_by_game_store_platform(session, sample_data):
    repo = GameOfferRepository(session)
    offer = await repo.get_by_game_store_platform(
        sample_data["game"].id,
        sample_data["store"].id,
        sample_data["platform"].id,
    )
    assert offer is not None
    assert offer.id == sample_data["offer"].id


@pytest.mark.asyncio
async def test_game_offer_repository_update_price(session, sample_data):
    repo = GameOfferRepository(session)
    updated = await repo.update_price(
        sample_data["offer"].id,
        "19.99",
        "29.99",
        "USD",
        True,
    )
    assert updated is not None
    assert updated.current_price == Decimal("19.99")
    assert updated.regular_price == Decimal("29.99")


@pytest.mark.asyncio
async def test_price_history_repository_get_by_offer(session, sample_data):
    repo = PriceHistoryRepository(session)
    history = PriceHistory(
        id=uuid4(),
        offer_id=sample_data["offer"].id,
        store_id=sample_data["store"].id,
        price=Decimal("29.99"),
        currency="USD",
        availability=True,
    )
    session.add(history)
    await session.commit()

    histories = await repo.get_by_offer(sample_data["offer"].id)
    assert len(histories) == 1
    assert histories[0].price == Decimal("29.99")


@pytest.mark.asyncio
async def test_price_history_repository_should_record_price(session, sample_data):
    repo = PriceHistoryRepository(session)

    should_record = await repo.should_record_price(
        sample_data["offer"].id,
        "29.99",
        "USD",
        True,
    )
    assert should_record is True

    history = PriceHistory(
        id=uuid4(),
        offer_id=sample_data["offer"].id,
        store_id=sample_data["store"].id,
        price=Decimal("29.99"),
        currency="USD",
        availability=True,
    )
    session.add(history)
    await session.commit()

    should_record = await repo.should_record_price(
        sample_data["offer"].id,
        "29.99",
        "USD",
        True,
    )
    assert should_record is False

    should_record = await repo.should_record_price(
        sample_data["offer"].id,
        "19.99",
        "USD",
        True,
    )
    assert should_record is True


@pytest.mark.asyncio
async def test_search_cache_repository_get_valid_cache(session):
    repo = SearchCacheRepository(session)
    cache = SearchCache(
        id=uuid4(),
        cache_key="valid-key",
        query="test",
        filters={},
        result_data={"data": "test"},
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    session.add(cache)
    await session.commit()

    found = await repo.get_valid_cache("valid-key")
    assert found is not None
    assert found.cache_key == "valid-key"


@pytest.mark.asyncio
async def test_search_cache_repository_expired_cache(session):
    repo = SearchCacheRepository(session)
    cache = SearchCache(
        id=uuid4(),
        cache_key="expired-key",
        query="test",
        filters={},
        result_data={"data": "test"},
        expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    session.add(cache)
    await session.commit()

    found = await repo.get_valid_cache("expired-key")
    assert found is None


@pytest.mark.asyncio
async def test_search_cache_repository_cleanup_expired(session):
    repo = SearchCacheRepository(session)
    cache1 = SearchCache(
        id=uuid4(),
        cache_key="expired-key",
        query="test",
        filters={},
        result_data={"data": "test"},
        expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    cache2 = SearchCache(
        id=uuid4(),
        cache_key="valid-key",
        query="test",
        filters={},
        result_data={"data": "test"},
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    session.add_all([cache1, cache2])
    await session.commit()

    deleted = await repo.cleanup_expired()
    assert deleted == 1