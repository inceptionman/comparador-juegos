import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Boolean,
    UniqueConstraint,
    JSON,
    func,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Game(Base, TimestampMixin):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)

    platforms: Mapped[List["Platform"]] = relationship(
        "Platform",
        secondary="game_platforms",
        back_populates="games",
        lazy="selectin",
    )
    offers: Mapped[List["GameOffer"]] = relationship(
        "GameOffer",
        back_populates="game",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_games_title_slug", "title", "slug"),
    )


class Platform(Base, TimestampMixin):
    __tablename__ = "platforms"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    games: Mapped[List["Game"]] = relationship(
        "Game",
        secondary="game_platforms",
        back_populates="platforms",
        lazy="selectin",
    )


class GamePlatform(Base):
    __tablename__ = "game_platforms"

    game_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
        primary_key=True,
    )
    platform_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("platforms.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Store(Base, TimestampMixin):
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    offers: Mapped[List["GameOffer"]] = relationship(
        "GameOffer",
        back_populates="store",
        lazy="selectin",
    )
    price_history: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory",
        back_populates="store",
        lazy="selectin",
    )


class GameOffer(Base, TimestampMixin):
    __tablename__ = "game_offers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stores.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    platform_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("platforms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    product_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    regular_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    game: Mapped["Game"] = relationship("Game", back_populates="offers", lazy="selectin")
    store: Mapped["Store"] = relationship("Store", back_populates="offers", lazy="selectin")
    platform: Mapped["Platform"] = relationship("Platform", lazy="selectin")
    price_history: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory",
        back_populates="offer",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("game_id", "store_id", "platform_id", "external_id", name="uq_game_store_platform_external"),
        Index("ix_game_offers_game_store_platform", "game_id", "store_id", "platform_id"),
        Index("ix_game_offers_last_checked", "last_checked_at"),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("game_offers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stores.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    regular_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    availability: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    offer: Mapped["GameOffer"] = relationship("GameOffer", back_populates="price_history", lazy="selectin")
    store: Mapped["Store"] = relationship("Store", back_populates="price_history", lazy="selectin")

    __table_args__ = (
        Index("ix_price_history_offer_recorded", "offer_id", "recorded_at"),
        Index("ix_price_history_store_recorded", "store_id", "recorded_at"),
    )


class SearchCache(Base, TimestampMixin):
    __tablename__ = "search_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    wishlist_items: Mapped[List["WishlistItem"]] = relationship(
        "WishlistItem",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class WishlistItem(Base, TimestampMixin):
    __tablename__ = "wishlist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="wishlist_items", lazy="selectin")
    game: Mapped["Game"] = relationship("Game", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_user_game_wishlist"),
    )
