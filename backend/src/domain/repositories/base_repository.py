"""Base repository interface — common CRUD contract for all aggregates."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.domain.entities.base_entity import BaseEntity

TEntity = TypeVar("TEntity", bound=BaseEntity)


class IRepository(ABC, Generic[TEntity]):
    """Abstract CRUD contract for a single aggregate type."""

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> TEntity | None: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> TEntity | None: ...

    @abstractmethod
    async def create(self, entity: TEntity) -> TEntity: ...

    @abstractmethod
    async def update(self, entity: TEntity) -> TEntity: ...

    @abstractmethod
    async def delete(self, entity_id: int) -> None: ...

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[TEntity]: ...

    @abstractmethod
    async def count(
        self,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> int: ...

    @abstractmethod
    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool: ...
