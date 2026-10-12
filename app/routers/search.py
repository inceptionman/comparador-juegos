import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.itad_client import buscar_juego, obtener_precios

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/buscar", response_class=HTMLResponse)
async def buscar(request: Request, q: str):
    ctx = {"resultado": None, "mensaje": None}
    try:
        juegos = await buscar_juego(q)
        if not juegos:
            ctx["mensaje"] = "No se encontró el juego."
        else:
            juego = juegos[0]
            data = await obtener_precios([juego["id"]])
            ofertas = []
            if data and data[0].get("deals"):
                ofertas = sorted(data[0]["deals"], key=lambda d: d["price"]["amount"])
            ctx["resultado"] = {"nombre": juego["title"], "ofertas": ofertas}
    except httpx.HTTPError:
        ctx["mensaje"] = "El servicio de precios no responde. Intenta de nuevo."
    return templates.TemplateResponse(request, "partials/resultado.html", ctx)

@router.get("/sugerencias", response_class=HTMLResponse)
async def sugerencias(request: Request, q: str = ""):
    juegos = []
    if len(q.strip()) >= 2:
        try:
            juegos = await buscar_juego(q, limite=5)
        except httpx.HTTPError:
            pass
    return templates.TemplateResponse(request, "partials/sugerencias.html", {"juegos": juegos})