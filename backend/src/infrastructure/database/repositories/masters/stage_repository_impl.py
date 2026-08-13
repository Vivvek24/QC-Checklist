"""Stage Master — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.masters.stage import Stage
from src.domain.repositories.masters.stage_repository import IStageRepository
from src.infrastructure.database.models.masters.stage_model import StageModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class StageRepositoryImpl(SqlAlchemyRepository[Stage, StageModel], IStageRepository):
    _model = StageModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(StageModel.stage_name) == code.lower()

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[Stage]:
        stmt = self._apply_filters(select(StageModel), search, is_active)
        stmt = stmt.order_by(StageModel.stage_name).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = self._apply_filters(select(func.count()).select_from(StageModel), search, is_active)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_name(code, exclude_id)

    async def exists_by_name(self, stage_name: str, exclude_id: int | None = None) -> bool:
        stmt = select(StageModel.id).where(func.lower(StageModel.stage_name) == stage_name.lower())
        if exclude_id is not None:
            stmt = stmt.where(StageModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, entity: Stage) -> Stage:
        model = StageModel(stage_name=entity.stage_name, is_active=entity.is_active, created_by=entity.created_by, modified_by=entity.modified_by)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: Stage) -> Stage:
        model = await self._require_model(entity.id)
        model.stage_name = entity.stage_name
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search:
            stmt = stmt.where(StageModel.stage_name.ilike(f"%{search.strip()}%"))
        if is_active is not None:
            stmt = stmt.where(StageModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(model: StageModel) -> Stage:
        return Stage(id=model.id, stage_name=model.stage_name, is_active=model.is_active,
                     created_by=model.created_by, created_date=model.created_date,
                     modified_by=model.modified_by, modified_date=model.modified_date)
