"""
Business Unit Master — repository implementation (infrastructure adapter).
"""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, or_, select

from src.domain.entities.masters.business_unit import BusinessUnit
from src.domain.repositories.masters.business_unit_repository import IBusinessUnitRepository
from src.infrastructure.database.models.masters.business_unit_model import BusinessUnitModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class BusinessUnitRepositoryImpl(
    SqlAlchemyRepository[BusinessUnit, BusinessUnitModel],
    IBusinessUnitRepository,
):
    """SQLAlchemy implementation of IBusinessUnitRepository."""

    _model = BusinessUnitModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        """Business units have no code — match on name instead."""
        return func.lower(BusinessUnitModel.name) == code.lower()

    # ─── Reads ───

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[BusinessUnit]:
        """List business units with pagination, free-text search and active filter."""
        stmt = self._apply_filters(select(BusinessUnitModel), search, is_active)
        stmt = stmt.order_by(BusinessUnitModel.name).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        """Count business units matching the same filters."""
        stmt = self._apply_filters(
            select(func.count()).select_from(BusinessUnitModel), search, is_active
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_by_code(self, code: str) -> BusinessUnit | None:
        """Retrieve a business unit by name (used as the unique business key)."""
        stmt = select(BusinessUnitModel).where(self._code_equals(code))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        """Check if a business unit name is taken."""
        stmt = select(BusinessUnitModel.id).where(self._code_equals(code))
        if exclude_id is not None:
            stmt = stmt.where(BusinessUnitModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool:
        """Check if a business unit name is taken (alias of exists_by_code)."""
        return await self.exists_by_code(name, exclude_id)

    # ─── Writes ───

    async def create(self, entity: BusinessUnit) -> BusinessUnit:
        """Persist a new business unit. DB generates the id."""
        model = BusinessUnitModel(
            name=entity.name,
            is_active=entity.is_active,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: BusinessUnit) -> BusinessUnit:
        """Update an existing business unit."""
        model = await self._require_model(entity.id)
        model.name = entity.name
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    # ─── Internals ───

    @staticmethod
    def _apply_filters(
        stmt: Select[Any],
        search: str | None,
        is_active: bool | None,
    ) -> Select[Any]:
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(BusinessUnitModel.name.ilike(pattern))
        if is_active is not None:
            stmt = stmt.where(BusinessUnitModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(model: BusinessUnitModel) -> BusinessUnit:
        """Map ORM model to domain entity."""
        return BusinessUnit(
            id=model.id,
            name=model.name,
            is_active=model.is_active,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
