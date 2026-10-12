"""Initial migration: create all tables

Revision ID: b9261a6b2203
Revises: 
Create Date: 2026-10-10 11:58:43.241807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9261a6b2203'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'platforms',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_platforms_slug', 'platforms', ['slug'], unique=True)

    op.create_table(
        'games',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('release_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('external_id'),
    )
    op.create_index('ix_games_title', 'games', ['title'], unique=False)
    op.create_index('ix_games_slug', 'games', ['slug'], unique=True)
    op.create_index('ix_games_external_id', 'games', ['external_id'], unique=True)
    op.create_index('ix_games_title_slug', 'games', ['title', 'slug'], unique=False)

    op.create_table(
        'game_platforms',
        sa.Column('game_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('platform_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('game_id', 'platform_id'),
    )

    op.create_table(
        'stores',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_stores_slug', 'stores', ['slug'], unique=True)

    op.create_table(
        'game_offers',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('game_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('store_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('platform_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('product_url', sa.String(length=1000), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('regular_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'store_id', 'platform_id', 'external_id', name='uq_game_store_platform_external'),
    )
    op.create_index('ix_game_offers_game_id', 'game_offers', ['game_id'], unique=False)
    op.create_index('ix_game_offers_store_id', 'game_offers', ['store_id'], unique=False)
    op.create_index('ix_game_offers_platform_id', 'game_offers', ['platform_id'], unique=False)
    op.create_index('ix_game_offers_external_id', 'game_offers', ['external_id'], unique=False)
    op.create_index('ix_game_offers_game_store_platform', 'game_offers', ['game_id', 'store_id', 'platform_id'], unique=False)
    op.create_index('ix_game_offers_last_checked', 'game_offers', ['last_checked_at'], unique=False)

    op.create_table(
        'price_history',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('offer_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('store_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('regular_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('availability', sa.Boolean(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['offer_id'], ['game_offers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_price_history_offer_id', 'price_history', ['offer_id'], unique=False)
    op.create_index('ix_price_history_store_id', 'price_history', ['store_id'], unique=False)
    op.create_index('ix_price_history_recorded_at', 'price_history', ['recorded_at'], unique=False)
    op.create_index('ix_price_history_offer_recorded', 'price_history', ['offer_id', 'recorded_at'], unique=False)
    op.create_index('ix_price_history_store_recorded', 'price_history', ['store_id', 'recorded_at'], unique=False)

    op.create_table(
        'search_cache',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('query', sa.String(length=500), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('result_data', sa.JSON(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key'),
    )
    op.create_index('ix_search_cache_cache_key', 'search_cache', ['cache_key'], unique=True)
    op.create_index('ix_search_cache_expires_at', 'search_cache', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_search_cache_expires_at', table_name='search_cache')
    op.drop_index('ix_search_cache_cache_key', table_name='search_cache')
    op.drop_table('search_cache')
    op.drop_index('ix_price_history_store_recorded', table_name='price_history')
    op.drop_index('ix_price_history_offer_recorded', table_name='price_history')
    op.drop_index('ix_price_history_recorded_at', table_name='price_history')
    op.drop_index('ix_price_history_store_id', table_name='price_history')
    op.drop_index('ix_price_history_offer_id', table_name='price_history')
    op.drop_table('price_history')
    op.drop_index('ix_game_offers_last_checked', table_name='game_offers')
    op.drop_index('ix_game_offers_game_store_platform', table_name='game_offers')
    op.drop_index('ix_game_offers_external_id', table_name='game_offers')
    op.drop_index('ix_game_offers_platform_id', table_name='game_offers')
    op.drop_index('ix_game_offers_store_id', table_name='game_offers')
    op.drop_index('ix_game_offers_game_id', table_name='game_offers')
    op.drop_table('game_offers')
    op.drop_index('ix_stores_slug', table_name='stores')
    op.drop_table('stores')
    op.drop_table('game_platforms')
    op.drop_index('ix_games_title_slug', table_name='games')
    op.drop_index('ix_games_external_id', table_name='games')
    op.drop_index('ix_games_slug', table_name='games')
    op.drop_index('ix_games_title', table_name='games')
    op.drop_table('games')
    op.drop_index('ix_platforms_slug', table_name='platforms')
    op.drop_table('platforms')