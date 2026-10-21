import httpx
from app.core.config import get_settings


settings = get_settings()


def _image_url_from_game(game: dict) -> str | None:
    """Obtiene la mejor imagen disponible en una respuesta de ITAD."""
    direct_image = game.get("image_url") or game.get("image")
    if isinstance(direct_image, str) and direct_image.strip():
        return direct_image.strip()

    assets = game.get("assets") or {}
    if isinstance(assets, dict):
        for asset_name in ("boxart", "banner300", "banner400", "banner145", "banner600"):
            asset_url = assets.get(asset_name)
            if isinstance(asset_url, str) and asset_url.strip():
                return asset_url.strip()
    return None


async def buscar_juego(titulo: str, limite: int = 10) -> list[dict]:
    """Busca juegos por título y normaliza su portada para la aplicación."""
    if not titulo.strip():
        return []
    if not settings.ITAD_API_KEY:
        raise httpx.HTTPError("ITAD_API_KEY is not configured")
    async with httpx.AsyncClient(timeout=settings.ITAD_TIMEOUT_SECONDS) as client:
        resp = await client.get(
            f"{settings.ITAD_BASE_URL}/games/search/v1",
            params={"key": settings.ITAD_API_KEY, "title": titulo, "results": limite},
        )
        resp.raise_for_status()
        games = resp.json()
        if not isinstance(games, list):
            return []

        normalized_games = []
        for game in games:
            if not isinstance(game, dict):
                continue
            normalized_game = dict(game)
            image_url = _image_url_from_game(game)
            if image_url:
                normalized_game["image_url"] = image_url
            normalized_games.append(normalized_game)
        return normalized_games


async def obtener_precios(game_ids: list[str], country: str = "US") -> list[dict]:
    """Dado un listado de IDs de ITAD, devuelve los precios actuales por tienda."""
    if not game_ids:
        return []
    if not settings.ITAD_API_KEY:
        raise httpx.HTTPError("ITAD_API_KEY is not configured")
    async with httpx.AsyncClient(timeout=settings.ITAD_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            f"{settings.ITAD_BASE_URL}/games/prices/v3",
            params={"key": settings.ITAD_API_KEY, "country": country, "deals": "true"},
            json=game_ids,
        )
        resp.raise_for_status()
        return resp.json()
