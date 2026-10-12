import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.cache.service import CacheService
from app.cache.database_cache import DatabaseCache
from app.cache.redis_cache import RedisCache
from app.db.models import SearchCache


@pytest.mark.asyncio
async def test_database_cache_get_set(session):
    cache = DatabaseCache(session)

    await cache.set("test-key", {"data": "test-value"}, 300)
    await session.commit()

    result = await cache.get("test-key")
    assert result == {"data": "test-value"}


@pytest.mark.asyncio
async def test_database_cache_get_nonexistent(session):
    cache = DatabaseCache(session)

    result = await cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_database_cache_delete(session):
    cache = DatabaseCache(session)

    await cache.set("test-key", {"data": "test"}, 300)
    await session.commit()

    deleted = await cache.delete("test-key")
    assert deleted is True

    result = await cache.get("test-key")
    assert result is None


@pytest.mark.asyncio
async def test_database_cache_exists(session):
    cache = DatabaseCache(session)

    await cache.set("test-key", {"data": "test"}, 300)
    await session.commit()

    exists = await cache.exists("test-key")
    assert exists is True

    exists = await cache.exists("nonexistent")
    assert exists is False


@pytest.mark.asyncio
async def test_database_cache_expired(session):
    cache = DatabaseCache(session)

    expired_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    search_cache = SearchCache(
        id=uuid4(),
        cache_key="expired-key",
        query="test",
        filters={},
        result_data={"data": "test"},
        expires_at=expired_at,
    )
    session.add(search_cache)
    await session.commit()

    result = await cache.get("expired-key")
    assert result is None


@pytest.mark.asyncio
async def test_database_cache_cleanup_expired(session):
    cache = DatabaseCache(session)

    expired_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    valid_at = datetime.now(timezone.utc) + timedelta(hours=1)

    expired = SearchCache(
        id=uuid4(),
        cache_key="expired-key",
        query="test",
        filters={},
        result_data={"data": "test"},
        expires_at=expired_at,
    )
    valid = SearchCache(
        id=uuid4(),
        cache_key="valid-key",
        query="test",
        filters={},
        result_data={"data": "test"},
        expires_at=valid_at,
    )
    session.add_all([expired, valid])
    await session.commit()

    deleted = await cache.cleanup_expired()
    assert deleted == 1


@pytest.mark.asyncio
async def test_cache_service_generate_key():
    service = CacheService()

    key1 = service._generate_key("query", {"filter": "value"})
    key2 = service._generate_key("query", {"filter": "value"})
    key3 = service._generate_key("query", {"filter": "other"})
    key4 = service._generate_key("other query", {"filter": "value"})

    assert key1 == key2
    assert key1 != key3
    assert key1 != key4
    assert len(key1) == 64


@pytest.mark.asyncio
async def test_cache_service_with_session(session):
    service = CacheService.with_session(session)

    await service.set("test query", {"results": ["game1"]}, {"platform": "pc"}, 300)
    await session.commit()

    result = await service.get("test query", {"platform": "pc"})
    assert result == {"results": ["game1"]}

    # Different filters should return None
    result = await service.get("test query", {"platform": "ps5"})
    assert result is None


@pytest.mark.asyncio
async def test_cache_service_delete(session):
    service = CacheService.with_session(session)

    await service.set("test query", {"results": ["game1"]}, {"platform": "pc"}, 300)
    await session.commit()

    deleted = await service.delete("test query", {"platform": "pc"})
    assert deleted is True

    result = await service.get("test query", {"platform": "pc"})
    assert result is None