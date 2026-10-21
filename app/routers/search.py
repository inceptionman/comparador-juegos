import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.itad_client import buscar_juego, obtener_precios
from app.db.base import get_session
from app.services.persistence import PersistenceService
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/buscar", response_class=HTMLResponse)
async def buscar(
    request: Request,
    q: str,
    session: AsyncSession = Depends(get_session),
):
    ctx = {"resultado": None, "mensaje": None}
    query = q.strip()
    if len(query) < 2:
        ctx["mensaje"] = "Escribe al menos dos caracteres para buscar."
        return templates.TemplateResponse(request, "partials/resultado.html", ctx)
    try:
        juegos = await buscar_juego(query)
        if not juegos:
            ctx["mensaje"] = "No se encontró el juego."
        else:
            juego = juegos[0]
            data = await obtener_precios([juego["id"]])
            price_result = data[0] if isinstance(data, list) and data else {}
            ofertas = [
                deal for deal in (price_result.get("deals") or [])
                if (deal.get("price") or {}).get("amount") is not None
            ]
            ofertas.sort(key=lambda deal: deal["price"]["amount"])
            game_id = None
            try:
                game = await PersistenceService(session).sync_external_game(juego, ofertas)
                game_id = str(game.id)
            except SQLAlchemyError:
                await session.rollback()
            ctx["resultado"] = {
                "nombre": juego.get("title", query),
                "image_url": juego.get("image_url"),
                "ofertas": ofertas,
                "game_id": game_id,
            }
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        ctx["mensaje"] = "El servicio de precios no responde. Intenta de nuevo."
    return templates.TemplateResponse(request, "partials/resultado.html", ctx)

@router.get("/sugerencias", response_class=HTMLResponse)
async def sugerencias(request: Request, q: str = ""):
    juegos = []
    if len(q.strip()) >= 2:
        try:
            juegos = await buscar_juego(q, limite=10)
        except httpx.HTTPError:
            pass
    return templates.TemplateResponse(request, "partials/sugerencias.html", {"juegos": juegos})
