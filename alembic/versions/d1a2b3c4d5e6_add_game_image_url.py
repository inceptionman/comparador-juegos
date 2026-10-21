"""add image URL to games

Revision ID: d1a2b3c4d5e6
Revises: 93fca38e0e3d
Create Date: 2026-10-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1a2b3c4d5e6"
down_revision: Union[str, None] = "93fca38e0e3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games", sa.Column("image_url", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("games", "image_url")
