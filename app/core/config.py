import os
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()


ITAD_API_KEY = os.getenv("ITAD_API_KEY", "")
ITAD_BASE_URL = "https://api.isthereanydeal.com"


class Settings:
    ITAD_API_KEY: str = ITAD_API_KEY
    ITAD_BASE_URL: str = ITAD_BASE_URL

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
    DATABASE_URL_SYNC: str = os.getenv("DATABASE_URL_SYNC", "sqlite:///./dev.db")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", str(60 * 24 * 7)))
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "").lower() == "true"
    ITAD_TIMEOUT_SECONDS: float = float(os.getenv("ITAD_TIMEOUT_SECONDS", "10"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
