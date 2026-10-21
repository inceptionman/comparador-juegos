from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base, get_session
from app.db.models import Game, GameOffer, GamePlatform, Platform, Store
from app.main import app


@pytest_asyncio.fixture
async def api_client(tmp_path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'api.db'}"
    engine = create_async_engine(database_url)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_session

    async with session_maker() as session:
        game = Game(id=uuid4(), title="Juego de prueba", slug="juego-de-prueba")
        platform = Platform(id=uuid4(), name="PC", slug="pc")
        store = Store(id=uuid4(), name="Tienda de prueba", slug="tienda-de-prueba")
        session.add_all([game, platform, store])
        await session.flush()
        session.add(GamePlatform(game_id=game.id, platform_id=platform.id))
        session.add(
            GameOffer(
                id=uuid4(),
                game_id=game.id,
                store_id=store.id,
                platform_id=platform.id,
                currency="USD",
                current_price=Decimal("19.99"),
                is_available=True,
            )
        )
        await session.commit()
        game_id = str(game.id)

    with TestClient(app) as client:
        yield client, game_id

    app.dependency_overrides.clear()
    await engine.dispose()


def test_authentication_and_wishlist_flow(api_client):
    client, game_id = api_client

    register = client.post(
        "/api/auth/register",
        json={"name": "Ana", "email": "ANA@example.com", "password": "password123"},
    )
    assert register.status_code == 200
    assert client.get("/api/auth/me").json()["email"] == "ana@example.com"
    assert client.get("/api/wishlist/page").status_code == 200

    added = client.post(
        "/api/wishlist",
        json={"game_id": game_id, "target_price": 20, "currency": "usd"},
    )
    assert added.status_code == 201
    assert added.json()["target_reached"] is True
    assert added.json()["current_price_currency"] == "USD"

    duplicate = client.post(
        "/api/wishlist",
        json={"game_id": game_id, "target_price": 10, "currency": "USD"},
    )
    assert duplicate.status_code == 409

    different_currency = client.patch(
        f"/api/wishlist/{added.json()['id']}",
        json={"target_price": 100, "currency": "COP"},
    )
    assert different_currency.status_code == 200
    assert different_currency.json()["current_price"] is None
    assert different_currency.json()["target_reached"] is False


def test_wishlist_rejects_non_finite_price(api_client):
    client, game_id = api_client
    client.post(
        "/api/auth/register",
        json={"name": "Luis", "email": "luis@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/wishlist",
        json={"game_id": game_id, "target_price": "Infinity", "currency": "USD"},
    )
    assert response.status_code == 422
