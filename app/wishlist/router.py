from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.router import get_current_user
from app.db.base import get_session
from app.db.models import Game, GameOffer, WishlistItem

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])
templates = Jinja2Templates(directory="app/templates")


class WishlistItemCreate(BaseModel):
    game_id: UUID
    target_price: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class WishlistItemUpdate(BaseModel):
    target_price: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


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


def get_best_offer(game: Game) -> Optional[GameOffer]:
    available_offers = [o for o in game.offers if o.is_available]
    if not available_offers:
        return None
    return min(available_offers, key=lambda o: o.current_price)


@router.get("", response_model=List[WishlistItemResponse])
async def get_wishlist(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(WishlistItem)
        .where(WishlistItem.user_id == current_user.id)
        .options(selectinload(WishlistItem.game).selectinload(Game.offers).selectinload(GameOffer.store))
    )
    items = result.scalars().all()

    response = []
    for item in items:
        game = item.game
        best_offer = get_best_offer(game)

        response.append(
            WishlistItemResponse(
                id=item.id,
                game_id=game.id,
                game_title=game.title,
                game_slug=game.slug,
                platform_name=", ".join(p.name for p in game.platforms) if game.platforms else None,
                image_url=None,
                target_price=item.target_price,
                currency=item.currency,
                current_price=best_offer.current_price if best_offer else None,
                current_price_currency=best_offer.currency if best_offer else None,
                best_store_name=best_offer.store.name if best_offer else None,
                best_store_slug=best_offer.store.slug if best_offer else None,
                target_reached=bool(best_offer and best_offer.current_price <= item.target_price and best_offer.currency == item.currency),
                created_at=item.created_at.isoformat(),
            )
        )
    return response


@router.post("", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    data: WishlistItemCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    game = await session.get(Game, data.game_id, options=[selectinload(Game.offers).selectinload(GameOffer.store), selectinload(Game.platforms)])
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    existing = await session.execute(
        select(WishlistItem).where(WishlistItem.user_id == current_user.id, WishlistItem.game_id == data.game_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Game already in wishlist")

    item = WishlistItem(
        user_id=current_user.id,
        game_id=data.game_id,
        target_price=data.target_price,
        currency=data.currency,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    best_offer = get_best_offer(game)
    return WishlistItemResponse(
        id=item.id,
        game_id=game.id,
        game_title=game.title,
        game_slug=game.slug,
        platform_name=", ".join(p.name for p in game.platforms) if game.platforms else None,
        image_url=None,
        target_price=item.target_price,
        currency=item.currency,
        current_price=best_offer.current_price if best_offer else None,
        current_price_currency=best_offer.currency if best_offer else None,
        best_store_name=best_offer.store.name if best_offer else None,
        best_store_slug=best_offer.store.slug if best_offer else None,
        target_reached=bool(best_offer and best_offer.current_price <= item.target_price and best_offer.currency == item.currency),
        created_at=item.created_at.isoformat(),
    )


@router.patch("/{item_id}", response_model=WishlistItemResponse)
async def update_wishlist_item(
    item_id: UUID,
    data: WishlistItemUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    item = await session.get(WishlistItem, item_id, options=[selectinload(WishlistItem.game).selectinload(Game.offers).selectinload(GameOffer.store), selectinload(WishlistItem.game).selectinload(Game.platforms)])
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")

    if item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    item.target_price = data.target_price
    item.currency = data.currency
    await session.commit()
    await session.refresh(item)

    game = item.game
    best_offer = get_best_offer(game)
    return WishlistItemResponse(
        id=item.id,
        game_id=game.id,
        game_title=game.title,
        game_slug=game.slug,
        platform_name=", ".join(p.name for p in game.platforms) if game.platforms else None,
        image_url=None,
        target_price=item.target_price,
        currency=item.currency,
        current_price=best_offer.current_price if best_offer else None,
        current_price_currency=best_offer.currency if best_offer else None,
        best_store_name=best_offer.store.name if best_offer else None,
        best_store_slug=best_offer.store.slug if best_offer else None,
        target_reached=bool(best_offer and best_offer.current_price <= item.target_price and best_offer.currency == item.currency),
        created_at=item.created_at.isoformat(),
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wishlist(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    item = await session.get(WishlistItem, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")

    if item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    await session.delete(item)
    await session.commit()


@router.get("/{item_id}", response_model=WishlistItemResponse)
async def get_wishlist_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    item = await session.get(WishlistItem, item_id, options=[selectinload(WishlistItem.game).selectinload(Game.offers).selectinload(GameOffer.store), selectinload(WishlistItem.game).selectinload(Game.platforms)])
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")

    if item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    game = item.game
    best_offer = get_best_offer(game)
    return WishlistItemResponse(
        id=item.id,
        game_id=game.id,
        game_title=game.title,
        game_slug=game.slug,
        platform_name=", ".join(p.name for p in game.platforms) if game.platforms else None,
        image_url=None,
        target_price=item.target_price,
        currency=item.currency,
        current_price=best_offer.current_price if best_offer else None,
        current_price_currency=best_offer.currency if best_offer else None,
        best_store_name=best_offer.store.name if best_offer else None,
        best_store_slug=best_offer.store.slug if best_offer else None,
        target_reached=bool(best_offer and best_offer.current_price <= item.target_price and best_offer.currency == item.currency),
        created_at=item.created_at.isoformat(),
    )


@router.get("/page", response_class=HTMLResponse)
async def wishlist_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(request, "wishlist.html", {"user": current_user})