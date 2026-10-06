import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ITAD_BASE_URL = "https://api.isthereanydeal.com"
API_KEY = os.getenv("ITAD_API_KEY")


async def buscar_juego(titulo: str, limite: int = 5) -> list[dict]:
    """Busca juegos por título y devuelve una lista de resultados con id y nombre."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{ITAD_BASE_URL}/games/search/v1",
            params={"key": API_KEY, "title": titulo, "results": limite},
        )
        resp.raise_for_status()
        return resp.json()


async def obtener_precios(game_ids: list[str], country: str = "US") -> list[dict]:
    """Dado un listado de IDs de ITAD, devuelve los precios actuales por tienda."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{ITAD_BASE_URL}/games/prices/v3",
            params={"key": API_KEY, "country": country, "deals": "true"},
            json=game_ids,
        )
        resp.raise_for_status()
        return resp.json()