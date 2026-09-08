from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.itad_client import buscar_juego, obtener_precios

app = FastAPI(title="Comparador de Precios de Videojuegos")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"resultado": None}
    )


@app.get("/buscar", response_class=HTMLResponse)
async def buscar(request: Request, q: str):
    resultados = await buscar_juego(q)

    if not resultados:
        return templates.TemplateResponse(
            request=request,
            name="resultado.html",
            context={"resultado": None, "mensaje": "No se encontró el juego."}
        )

    # Tomamos el primer resultado como el más relevante
    juego = resultados[0]
    precios_data = await obtener_precios([juego["id"]])

    ofertas = []
    if precios_data and precios_data[0].get("deals"):
        ofertas = sorted(precios_data[0]["deals"], key=lambda d: d["price"]["amount"])

    return templates.TemplateResponse(
        request=request,
        name="resultado.html",
        context={
            "resultado": {"nombre": juego["title"], "ofertas": ofertas},
            "mensaje": None,
        }
    )