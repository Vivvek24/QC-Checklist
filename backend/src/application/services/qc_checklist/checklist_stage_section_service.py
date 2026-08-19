"""ChecklistStageSection — application service."""

from src.application.dtos.qc_checklist.checklist_stage_section_dtos import (
    ChecklistStageSectionDTO,
    ChecklistStageSectionListDTO,
    CreateChecklistStageSectionDTO,
    UpdateChecklistStageSectionDTO,
)
from src.domain.entities.qc_checklist.checklist_stage_section import ChecklistStageSection
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.domain.repositories.qc_checklist.checklist_stage_section_repository import IChecklistStageSectionRepository

ENTITY = "ChecklistStageSection"


class ChecklistStageSectionService:
    def __init__(self, repo: IChecklistStageSectionRepository) -> None:
        self._repo = repo

    async def list_sections(self, skip: int = 0, limit: int = 100) -> ChecklistStageSectionListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit)
        total = await self._repo.count()
        return ChecklistStageSectionListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[ChecklistStageSectionDTO]:
        items = await self._repo.list_by_checklist_stage(checklist_stage_id)
        return [self._to_dto(i) for i in items]

    async def get_section(self, section_id: int) -> ChecklistStageSectionDTO:
        return self._to_dto(await self._require(section_id))

    async def create_section(self, dto: CreateChecklistStageSectionDTO, actor: User) -> ChecklistStageSectionDTO:
        created = await self._repo.create(ChecklistStageSection(
            checklist_stage_id=dto.checklist_stage_id,
            section_id=dto.section_id,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_section(self, section_id: int, dto: UpdateChecklistStageSectionDTO, actor: User) -> ChecklistStageSectionDTO:
        entity = await self._require(section_id)
        if dto.checklist_stage_id is not None:
            entity.checklist_stage_id = dto.checklist_stage_id
        if dto.section_id is not None:
            entity.section_id = dto.section_id
        entity.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(entity))

    async def delete_section(self, section_id: int) -> None:
        await self._require(section_id)
        await self._repo.delete(section_id)

    async def _require(self, section_id: int) -> ChecklistStageSection:
        entity = await self._repo.get_by_id(section_id)
        if entity is None:
            raise EntityNotFoundError(ENTITY, section_id)
        return entity

    @staticmethod
    def _to_dto(e: ChecklistStageSection) -> ChecklistStageSectionDTO:
        return ChecklistStageSectionDTO(
            id=e.id,
            checklist_stage_id=e.checklist_stage_id,
            section_id=e.section_id,
            created_by=e.created_by,
            created_date=e.created_date,
            modified_by=e.modified_by,
            modified_date=e.modified_date,
        )
