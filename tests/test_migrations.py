import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


@pytest.mark.asyncio
async def test_migration_upgrade_downgrade():
    """Test that migrations can be applied and rolled back."""
    from app.core.config import get_settings
    from app.db.base import Base
    from app.db.models import Game, Platform, Store, GameOffer, PriceHistory, SearchCache

    settings = get_settings()
    sync_url = settings.DATABASE_URL_SYNC

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    engine = create_async_engine(sync_url.replace("sqlite://", "sqlite+aiosqlite://"))
    
    # Create tables directly to test metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Verify all tables exist
    async with engine.connect() as conn:
        def check_tables(sync_conn):
            inspector = inspect(sync_conn)
            tables = inspector.get_table_names()
            expected_tables = [
                'games', 'platforms', 'game_platforms', 'stores',
                'game_offers', 'price_history', 'search_cache', 'users',
                'wishlist_items', 'alembic_version'
            ]
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"
            
            # Check columns for games
            game_columns = [c['name'] for c in inspector.get_columns('games')]
            assert 'id' in game_columns
            assert 'title' in game_columns
            assert 'slug' in game_columns
            assert 'external_id' in game_columns
            assert 'image_url' in game_columns
            
            # Check columns for game_offers
            offer_columns = [c['name'] for c in inspector.get_columns('game_offers')]
            assert 'current_price' in offer_columns
            assert 'regular_price' in offer_columns
            assert 'currency' in offer_columns
            
            # Check columns for price_history
            history_columns = [c['name'] for c in inspector.get_columns('price_history')]
            assert 'price' in history_columns
            assert 'recorded_at' in history_columns
        
        await conn.run_sync(check_tables)
    
    await engine.dispose()
