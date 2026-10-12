from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def get_by_id(self, id: UUID) -> T | None:
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        pass

    @abstractmethod
    async def create(self, obj: T) -> T:
        pass

    @abstractmethod
    async def update(self, obj: T) -> T:
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        pass