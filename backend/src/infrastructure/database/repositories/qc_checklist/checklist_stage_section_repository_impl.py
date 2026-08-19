"""ChecklistStageSection — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.qc_checklist.checklist_stage_section import ChecklistStageSection
from src.domain.repositories.qc_checklist.checklist_stage_section_repository import IChecklistStageSectionRepository
from src.infrastructure.database.models.qc_checklist.checklist_stage_section_model import ChecklistStageSectionModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class ChecklistStageSectionRepositoryImpl(SqlAlchemyRepository[ChecklistStageSection, ChecklistStageSectionModel], IChecklistStageSectionRepository):
    _model = ChecklistStageSectionModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return ChecklistStageSectionModel.id == -1

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[ChecklistStageSection]:
        stmt = select(ChecklistStageSectionModel).order_by(ChecklistStageSectionModel.id.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = select(func.count()).select_from(ChecklistStageSectionModel)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return False

    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[ChecklistStageSection]:
        stmt = select(ChecklistStageSectionModel).where(
            ChecklistStageSectionModel.checklist_stage_id == checklist_stage_id
        ).order_by(ChecklistStageSectionModel.id)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: ChecklistStageSection) -> ChecklistStageSection:
        model = ChecklistStageSectionModel(
            checklist_stage_id=entity.checklist_stage_id,
            section_id=entity.section_id,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: ChecklistStageSection) -> ChecklistStageSection:
        model = await self._require_model(entity.id)
        model.checklist_stage_id = entity.checklist_stage_id
        model.section_id = entity.section_id
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: ChecklistStageSectionModel) -> ChecklistStageSection:
        return ChecklistStageSection(
            id=model.id,
            checklist_stage_id=model.checklist_stage_id,
            section_id=model.section_id,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
