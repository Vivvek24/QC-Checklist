"""Unit Master — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.masters.unit import Unit
from src.domain.repositories.masters.unit_repository import IUnitRepository
from src.infrastructure.database.models.masters.unit_model import UnitModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class UnitRepositoryImpl(
    SqlAlchemyRepository[Unit, UnitModel],
    IUnitRepository,
):
    _model = UnitModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(UnitModel.name) == code.lower()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Unit]:
        stmt = self._apply_filters(select(UnitModel), search, is_active)
        stmt = stmt.order_by(UnitModel.business_unit_id, UnitModel.name).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        stmt = self._apply_filters(
            select(func.count()).select_from(UnitModel), search, is_active
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        stmt = select(UnitModel.id).where(self._code_equals(code))
        if exclude_id is not None:
            stmt = stmt.where(UnitModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_name_in_business_unit(
        self, name: str, business_unit_id: int, exclude_id: int | None = None
    ) -> bool:
        stmt = select(UnitModel.id).where(
            func.lower(UnitModel.name) == name.lower(),
            UnitModel.business_unit_id == business_unit_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(UnitModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_by_business_unit(
        self, business_unit_id: int, is_active: bool | None = None
    ) -> list[Unit]:
        stmt = select(UnitModel).where(UnitModel.business_unit_id == business_unit_id)
        if is_active is not None:
            stmt = stmt.where(UnitModel.is_active.is_(is_active))
        stmt = stmt.order_by(UnitModel.name)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: Unit) -> Unit:
        model = UnitModel(
            name=entity.name,
            business_unit_id=entity.business_unit_id,
            is_active=entity.is_active,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: Unit) -> Unit:
        model = await self._require_model(entity.id)
        model.name = entity.name
        model.business_unit_id = entity.business_unit_id
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(
        stmt: Select[Any],
        search: str | None,
        is_active: bool | None,
    ) -> Select[Any]:
        if search:
            stmt = stmt.where(UnitModel.name.ilike(f"%{search.strip()}%"))
        if is_active is not None:
            stmt = stmt.where(UnitModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(model: UnitModel) -> Unit:
        return Unit(
            id=model.id,
            name=model.name,
            business_unit_id=model.business_unit_id,
            is_active=model.is_active,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
