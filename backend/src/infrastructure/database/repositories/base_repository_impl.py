"""Base repository implementation with common BigInt-keyed CRUD operations."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.base_entity import BaseEntity
from src.infrastructure.database.models.base_model import BaseModel

TEntity = TypeVar("TEntity", bound=BaseEntity)
TModel = TypeVar("TModel", bound=BaseModel)


class SqlAlchemyRepository(ABC, Generic[TEntity, TModel]):

    _model: type[TModel]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    @abstractmethod
    def _to_entity(model: TModel) -> TEntity: ...

    @staticmethod
    @abstractmethod
    def _code_equals(code: str) -> ColumnElement[bool]: ...

    async def get_by_id(self, entity_id: int) -> TEntity | None:
        model = await self._get_model(entity_id)
        return self._to_entity(model) if model else None

    async def get_by_code(self, code: str) -> TEntity | None:
        stmt = select(self._model).where(self._code_equals(code))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        stmt = select(self._model.id).where(self._code_equals(code))
        if exclude_id is not None:
            stmt = stmt.where(self._model.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete(self, entity_id: int) -> None:
        model = await self._get_model(entity_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def _get_model(self, entity_id: int) -> TModel | None:
        stmt = select(self._model).where(self._model.id == entity_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _require_model(self, entity_id: int) -> TModel:
        model = await self._get_model(entity_id)
        if model is None:
            raise ValueError(f"{self._model.__name__} with id {entity_id} not found")
        return model
