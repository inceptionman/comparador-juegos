from decimal import Decimal, InvalidOperation
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.router import get_current_user
from app.db.base import get_session
from app.db.models import Game, GameOffer, User, WishlistItem


router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])
templates = Jinja2Templates(directory="app/templates")
MAX_PRICE = Decimal("99999999.99")


def _game_image_url(game: Game) -> Optional[str]:
    """Return the stored cover or a stable ITAD cover fallback for legacy rows."""
    if game.image_url:
        return game.image_url
    if game.external_id:
        return f"https://assets.isthereanydeal.com/{game.external_id}/boxart.jpg"
    return None


def _validate_price(value: object) -> Decimal:
    try:
        price = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("target_price must be a valid number")
    if not price.is_finite():
        raise ValueError("target_price must be finite")
    if price < 0:
        raise ValueError("target_price must be greater than or equal to zero")
    if price > MAX_PRICE:
        raise ValueError("target_price is too large")
    if abs(price.as_tuple().exponent) > 2:
        raise ValueError("target_price supports at most two decimal places")
    return price


def _validate_currency(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("currency must be a three-letter code")
    currency = value.strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError("currency must be a three-letter code")
    return currency


class WishlistItemCreate(BaseModel):
    game_id: UUID
    target_price: Decimal = Field(ge=0)
    currency: str = Field(default="USD")

    _price = field_validator("target_price", mode="before")(_validate_price)
    _currency = field_validator("currency", mode="before")(_validate_currency)


class WishlistItemUpdate(BaseModel):
    target_price: Decimal = Field(ge=0)
    currency: str = Field(default="USD")

    _price = field_validator("target_price", mode="before")(_validate_price)
    _currency = field_validator("currency", mode="before")(_validate_currency)


class WishlistItemResponse(BaseModel):
    id: UUID
    game_id: UUID
    game_title: str
    game_slug: str
    platform_name: Optional[str]
    image_url: Optional[str]
    target_price: Decimal
    currency: str
    current_price: Optional[Decimal]
    current_price_currency: Optional[str]
    best_store_name: Optional[str]
    best_store_slug: Optional[str]
    target_reached: bool
    created_at: str


def get_best_offer(game: Game, currency: str) -> Optional[GameOffer]:
    """Return the cheapest available offer in the requested currency only."""
    available_offers = [
        offer
        for offer in game.offers
        if offer.is_available and offer.currency.upper() == currency
    ]
    if not available_offers:
        return None
    return min(available_offers, key=lambda offer: offer.current_price)


def _to_response(item: WishlistItem) -> WishlistItemResponse:
    game = item.game
    best_offer = get_best_offer(game, item.currency)
    return WishlistItemResponse(
        id=item.id,
        game_id=game.id,
        game_title=game.title,
        game_slug=game.slug,
        platform_name=", ".join(platform.name for platform in game.platforms) if game.platforms else None,
        image_url=_game_image_url(game),
        target_price=item.target_price,
        currency=item.currency,
        current_price=best_offer.current_price if best_offer else None,
        current_price_currency=best_offer.currency if best_offer else None,
        best_store_name=best_offer.store.name if best_offer and best_offer.store else None,
        best_store_slug=best_offer.store.slug if best_offer and best_offer.store else None,
        target_reached=bool(best_offer and best_offer.current_price <= item.target_price),
        created_at=item.created_at.isoformat(),
    )


GAME_OPTIONS = [
    selectinload(WishlistItem.game).selectinload(Game.offers).selectinload(GameOffer.store),
    selectinload(WishlistItem.game).selectinload(Game.platforms),
]


@router.get("/page", response_class=HTMLResponse)
async def wishlist_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(request, "wishlist.html", {"user": current_user})


@router.get("", response_model=List[WishlistItemResponse])
async def get_wishlist(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(WishlistItem)
        .where(WishlistItem.user_id == current_user.id)
        .options(*GAME_OPTIONS)
        .order_by(WishlistItem.created_at.desc())
    )
    return [_to_response(item) for item in result.scalars().all()]


@router.post("", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    data: WishlistItemCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    game = await session.get(
        Game,
        data.game_id,
        options=[
            selectinload(Game.offers).selectinload(GameOffer.store),
            selectinload(Game.platforms),
        ],
    )
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    existing = await session.scalar(
        select(WishlistItem).where(
            WishlistItem.user_id == current_user.id,
            WishlistItem.game_id == data.game_id,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game already in wishlist")

    item = WishlistItem(
        user_id=current_user.id,
        game_id=data.game_id,
        target_price=data.target_price,
        currency=data.currency,
    )
    session.add(item)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game already in wishlist")
    await session.refresh(item)
    return _to_response(item)


async def _get_item_for_user(item_id: UUID, current_user: User, session: AsyncSession) -> WishlistItem:
    item = await session.get(WishlistItem, item_id, options=GAME_OPTIONS)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")
    if item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return item


@router.patch("/{item_id}", response_model=WishlistItemResponse)
async def update_wishlist_item(
    item_id: UUID,
    data: WishlistItemUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    item = await _get_item_for_user(item_id, current_user, session)
    item.target_price = data.target_price
    item.currency = data.currency
    await session.commit()
    await session.refresh(item)
    return _to_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wishlist(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    item = await _get_item_for_user(item_id, current_user, session)
    await session.delete(item)
    await session.commit()


@router.get("/{item_id}", response_model=WishlistItemResponse)
async def get_wishlist_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    item = await _get_item_for_user(item_id, current_user, session)
    return _to_response(item)
