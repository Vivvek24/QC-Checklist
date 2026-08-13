"""FormatStageMapping — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.masters.format_stage_mapping import FormatStageMapping
from src.domain.repositories.masters.format_stage_mapping_repository import IFormatStageMappingRepository
from src.infrastructure.database.models.masters.format_stage_mapping_model import FormatStageMappingModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class FormatStageMappingRepositoryImpl(SqlAlchemyRepository[FormatStageMapping, FormatStageMappingModel], IFormatStageMappingRepository):
    _model = FormatStageMappingModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        # Not applicable for this entity — use exists_by_format_and_stage instead
        return FormatStageMappingModel.id == -1

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[FormatStageMapping]:
        stmt = self._apply_filters(select(FormatStageMappingModel), search, is_active)
        stmt = stmt.order_by(FormatStageMappingModel.id).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = self._apply_filters(select(func.count()).select_from(FormatStageMappingModel), search, is_active)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_by_format(self, format_id: int) -> list[FormatStageMapping]:
        stmt = select(FormatStageMappingModel).where(
            FormatStageMappingModel.format_id == format_id
        ).order_by(FormatStageMappingModel.id)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_stage(self, stage_id: int) -> list[FormatStageMapping]:
        stmt = select(FormatStageMappingModel).where(
            FormatStageMappingModel.stage_id == stage_id
        ).order_by(FormatStageMappingModel.id)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return False

    async def exists_by_format_and_stage(self, format_id: int, stage_id: int, exclude_id: int | None = None) -> bool:
        stmt = select(FormatStageMappingModel.id).where(
            FormatStageMappingModel.format_id == format_id,
            FormatStageMappingModel.stage_id == stage_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(FormatStageMappingModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, entity: FormatStageMapping) -> FormatStageMapping:
        model = FormatStageMappingModel(
            format_id=entity.format_id,
            stage_id=entity.stage_id,
            is_active=entity.is_active,
            is_approvable=entity.is_approvable,
            is_refer_back=entity.is_refer_back,
            has_section=entity.has_section,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: FormatStageMapping) -> FormatStageMapping:
        model = await self._require_model(entity.id)
        model.format_id = entity.format_id
        model.stage_id = entity.stage_id
        model.is_active = entity.is_active
        model.is_approvable = entity.is_approvable
        model.is_refer_back = entity.is_refer_back
        model.has_section = entity.has_section
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if is_active is not None:
            stmt = stmt.where(FormatStageMappingModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(model: FormatStageMappingModel) -> FormatStageMapping:
        return FormatStageMapping(
            id=model.id,
            format_id=model.format_id,
            stage_id=model.stage_id,
            is_active=model.is_active,
            is_approvable=model.is_approvable,
            is_refer_back=model.is_refer_back,
            has_section=model.has_section,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
