from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.router import get_current_user_optional
from app.db.base import get_session
from app.db.models import Game, GameOffer, Store, Platform, User, WishlistItem

router = APIRouter(prefix="/api/home", tags=["home"])


class GameCardResponse(BaseModel):
    id: str
    title: str
    slug: str
    platform: Optional[str]
    image_url: Optional[str]
    current_price: Optional[float]
    regular_price: Optional[float]
    currency: str
    discount_pct: Optional[int]
    store_name: Optional[str]
    store_slug: Optional[str]
    product_url: Optional[str]
    in_wishlist: bool = False


class HomeDataResponse(BaseModel):
    featured_deals: List[GameCardResponse]
    top_discounts: List[GameCardResponse]
    popular_games: List[GameCardResponse]
    new_releases: List[GameCardResponse]


def _build_game_card(offer: GameOffer, in_wishlist: bool = False) -> GameCardResponse:
    discount_pct = None
    if offer.regular_price and offer.regular_price > 0:
        discount_pct = int(round((1 - float(offer.current_price) / float(offer.regular_price)) * 100))
        discount_pct = max(0, min(100, discount_pct))

    platform_names = [p.name for p in offer.game.platforms] if offer.game.platforms else []

    return GameCardResponse(
        id=str(offer.game.id),
        title=offer.game.title,
        slug=offer.game.slug,
        platform=", ".join(platform_names) if platform_names else None,
        image_url=None,
        current_price=float(offer.current_price) if offer.current_price else None,
        regular_price=float(offer.regular_price) if offer.regular_price else None,
        currency=offer.currency,
        discount_pct=discount_pct,
        store_name=offer.store.name if offer.store else None,
        store_slug=offer.store.slug if offer.store else None,
        product_url=offer.product_url,
        in_wishlist=in_wishlist,
    )


@router.get("/featured-deals", response_model=List[GameCardResponse])
async def get_featured_deals(
    limit: int = Query(8, ge=1, le=20),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
):
    wishlist_game_ids = set()
    if current_user:
        result = await session.execute(
            select(WishlistItem.game_id).where(WishlistItem.user_id == current_user.id)
        )
        wishlist_game_ids = {row[0] for row in result.all()}

    result = await session.execute(
        select(GameOffer)
        .where(GameOffer.is_available == True)
        .options(
            selectinload(GameOffer.game).selectinload(Game.platforms),
            selectinload(GameOffer.store),
        )
        .order_by(GameOffer.current_price.asc())
        .limit(limit * 3)
    )
    offers = result.scalars().all()

    seen_games = set()
    featured = []
    for offer in offers:
        if offer.game_id in seen_games:
            continue
        seen_games.add(offer.game_id)
        featured.append(_build_game_card(offer, offer.game_id in wishlist_game_ids))
        if len(featured) >= limit:
            break

    return featured


@router.get("/top-discounts", response_model=List[GameCardResponse])
async def get_top_discounts(
    limit: int = Query(10, ge=1, le=30),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
):
    wishlist_game_ids = set()
    if current_user:
        result = await session.execute(
            select(WishlistItem.game_id).where(WishlistItem.user_id == current_user.id)
        )
        wishlist_game_ids = {row[0] for row in result.all()}

    result = await session.execute(
        select(GameOffer)
        .where(
            GameOffer.is_available == True,
            GameOffer.regular_price != None,
            GameOffer.regular_price > 0,
            GameOffer.current_price < GameOffer.regular_price,
        )
        .options(
            selectinload(GameOffer.game).selectinload(Game.platforms),
            selectinload(GameOffer.store),
        )
        .order_by(
            ((GameOffer.regular_price - GameOffer.current_price) / GameOffer.regular_price).desc()
        )
        .limit(limit * 3)
    )
    offers = result.scalars().all()

    seen_games = set()
    discounts = []
    for offer in offers:
        if offer.game_id in seen_games:
            continue
        seen_games.add(offer.game_id)
        discounts.append(_build_game_card(offer, offer.game_id in wishlist_game_ids))
        if len(discounts) >= limit:
            break

    return discounts


@router.get("/popular-games", response_model=List[GameCardResponse])
async def get_popular_games(
    limit: int = Query(6, ge=1, le=20),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
):
    wishlist_game_ids = set()
    if current_user:
        result = await session.execute(
            select(WishlistItem.game_id).where(WishlistItem.user_id == current_user.id)
        )
        wishlist_game_ids = {row[0] for row in result.all()}

    subquery = (
        select(WishlistItem.game_id, func.count(WishlistItem.id).label("wishlist_count"))
        .group_by(WishlistItem.game_id)
        .subquery()
    )

    result = await session.execute(
        select(GameOffer)
        .join(subquery, GameOffer.game_id == subquery.c.game_id)
        .where(GameOffer.is_available == True)
        .options(
            selectinload(GameOffer.game).selectinload(Game.platforms),
            selectinload(GameOffer.store),
        )
        .order_by(desc(subquery.c.wishlist_count), GameOffer.current_price.asc())
        .limit(limit * 3)
    )
    offers = result.scalars().all()

    seen_games = set()
    popular = []
    for offer in offers:
        if offer.game_id in seen_games:
            continue
        seen_games.add(offer.game_id)
        popular.append(_build_game_card(offer, offer.game_id in wishlist_game_ids))
        if len(popular) >= limit:
            break

    if len(popular) < limit:
        result = await session.execute(
            select(GameOffer)
            .where(GameOffer.is_available == True)
            .options(
                selectinload(GameOffer.game).selectinload(Game.platforms),
                selectinload(GameOffer.store),
            )
            .order_by(GameOffer.last_checked_at.desc())
            .limit((limit - len(popular)) * 3)
        )
        more_offers = result.scalars().all()
        for offer in more_offers:
            if offer.game_id in seen_games:
                continue
            seen_games.add(offer.game_id)
            popular.append(_build_game_card(offer, offer.game_id in wishlist_game_ids))
            if len(popular) >= limit:
                break

    return popular


@router.get("/new-releases", response_model=List[GameCardResponse])
async def get_new_releases(
    limit: int = Query(6, ge=1, le=20),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
):
    wishlist_game_ids = set()
    if current_user:
        result = await session.execute(
            select(WishlistItem.game_id).where(WishlistItem.user_id == current_user.id)
        )
        wishlist_game_ids = {row[0] for row in result.all()}

    result = await session.execute(
        select(GameOffer)
        .where(GameOffer.is_available == True)
        .options(
            selectinload(GameOffer.game).selectinload(Game.platforms),
            selectinload(GameOffer.store),
        )
        .order_by(GameOffer.game.has(Game.release_date.desc().nullslast()))
        .limit(limit * 3)
    )
    offers = result.scalars().all()

    seen_games = set()
    new_releases = []
    for offer in offers:
        if offer.game_id in seen_games:
            continue
        seen_games.add(offer.game_id)
        new_releases.append(_build_game_card(offer, offer.game_id in wishlist_game_ids))
        if len(new_releases) >= limit:
            break

    return new_releases


@router.get("/all", response_model=HomeDataResponse)
async def get_all_home_data(
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
):
    featured = await get_featured_deals(8, current_user, session)
    discounts = await get_top_discounts(10, current_user, session)
    popular = await get_popular_games(6, current_user, session)
    new = await get_new_releases(6, current_user, session)

    return HomeDataResponse(
        featured_deals=featured,
        top_discounts=discounts,
        popular_games=popular,
        new_releases=new,
    )