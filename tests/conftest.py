import pytest
import pytest_asyncio
import uuid
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.models import Game, Platform, Store, GameOffer, PriceHistory, SearchCache


@pytest_asyncio.fixture
async def engine():
    db_name = f"test_{uuid.uuid4().hex}.db"
    db_url = f"sqlite+aiosqlite:///{db_name}"
    
    engine = create_async_engine(
        db_url,
        echo=False,
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    
    if os.path.exists(db_name):
        os.remove(db_name)


@pytest_asyncio.fixture
async def session(engine) -> AsyncSession:
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()
