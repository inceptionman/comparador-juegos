"""add users and wishlist items tables

Revision ID: 93fca38e0e3d
Revises: b9261a6b2203
Create Date: 2026-10-11 07:00:51.165082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93fca38e0e3d'
down_revision: Union[str, None] = 'b9261a6b2203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'wishlist_items',
        sa.Column('id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('game_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('target_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'game_id', name='uq_user_game_wishlist'),
    )
    op.create_index('ix_wishlist_items_user_id', 'wishlist_items', ['user_id'], unique=False)
    op.create_index('ix_wishlist_items_game_id', 'wishlist_items', ['game_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_wishlist_items_game_id', table_name='wishlist_items')
    op.drop_index('ix_wishlist_items_user_id', table_name='wishlist_items')
    op.drop_table('wishlist_items')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')