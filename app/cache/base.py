from abc import ABC, abstractmethod
from typing import Any, Optional
import json


class CacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass