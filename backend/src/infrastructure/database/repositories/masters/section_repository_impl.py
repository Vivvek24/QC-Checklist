"""Section Master — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.masters.section import Section
from src.domain.repositories.masters.section_repository import ISectionRepository
from src.infrastructure.database.models.masters.section_model import SectionModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class SectionRepositoryImpl(SqlAlchemyRepository[Section, SectionModel], ISectionRepository):
    _model = SectionModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(SectionModel.section_name) == code.lower()

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None, format_stage_mapping_id: int | None = None) -> list[Section]:
        stmt = self._apply_filters(select(SectionModel), search, is_active, format_stage_mapping_id)
        stmt = stmt.order_by(SectionModel.section_name).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None, format_stage_mapping_id: int | None = None) -> int:
        stmt = self._apply_filters(select(func.count()).select_from(SectionModel), search, is_active, format_stage_mapping_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_name(code, exclude_id)

    async def exists_by_name(self, section_name: str, exclude_id: int | None = None) -> bool:
        stmt = select(SectionModel.id).where(func.lower(SectionModel.section_name) == section_name.lower())
        if exclude_id is not None:
            stmt = stmt.where(SectionModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, entity: Section) -> Section:
        model = SectionModel(
            section_name=entity.section_name,
            format_stage_mapping_id=entity.format_stage_mapping_id,
            is_active=entity.is_active,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: Section) -> Section:
        model = await self._require_model(entity.id)
        model.section_name = entity.section_name
        model.format_stage_mapping_id = entity.format_stage_mapping_id
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None, format_stage_mapping_id: int | None = None) -> Select[Any]:
        if search:
            stmt = stmt.where(SectionModel.section_name.ilike(f"%{search.strip()}%"))
        if is_active is not None:
            stmt = stmt.where(SectionModel.is_active.is_(is_active))
        if format_stage_mapping_id is not None:
            stmt = stmt.where(SectionModel.format_stage_mapping_id == format_stage_mapping_id)
        return stmt

    @staticmethod
    def _to_entity(model: SectionModel) -> Section:
        return Section(
            id=model.id,
            section_name=model.section_name,
            format_stage_mapping_id=model.format_stage_mapping_id,
            is_active=model.is_active,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
