"""ChecklistStage — application service."""

from src.application.dtos.qc_checklist.checklist_stage_dtos import (
    ChecklistStageDTO,
    ChecklistStageListDTO,
    CreateChecklistStageDTO,
    UpdateChecklistStageDTO,
)
from src.domain.entities.qc_checklist.checklist_stage import ChecklistStage
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.domain.repositories.qc_checklist.checklist_stage_repository import IChecklistStageRepository

ENTITY = "ChecklistStage"


class ChecklistStageService:
    def __init__(self, repo: IChecklistStageRepository) -> None:
        self._repo = repo

    async def list_stages(
        self, skip: int = 0, limit: int = 100, search: str | None = None
    ) -> ChecklistStageListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search)
        total = await self._repo.count(search=search)
        return ChecklistStageListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def list_by_checklist_request(self, checklist_request_id: int) -> list[ChecklistStageDTO]:
        items = await self._repo.list_by_checklist_request(checklist_request_id)
        return [self._to_dto(i) for i in items]

    async def get_stage(self, stage_id: int) -> ChecklistStageDTO:
        return self._to_dto(await self._require(stage_id))

    async def create_stage(self, dto: CreateChecklistStageDTO, actor: User) -> ChecklistStageDTO:
        created = await self._repo.create(ChecklistStage(
            checklist_request_id=dto.checklist_request_id,
            user_id=dto.user_id,
            format_stage_mapping_id=dto.format_stage_mapping_id,
            status=dto.status,
            performed_remark=dto.performed_remark,
            approved_remark=dto.approved_remark,
            is_self_verified=dto.is_self_verified,
            self_verification_details=dto.self_verification_details,
            is_approvable=dto.is_approvable,
            is_last_stage=dto.is_last_stage,
            submit_remarks=dto.submit_remarks,
            self_approved_remark=dto.self_approved_remark,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_stage(self, stage_id: int, dto: UpdateChecklistStageDTO, actor: User) -> ChecklistStageDTO:
        entity = await self._require(stage_id)
        if dto.status is not None:
            entity.status = dto.status
        if dto.user_id is not None:
            entity.user_id = dto.user_id
        if dto.format_stage_mapping_id is not None:
            entity.format_stage_mapping_id = dto.format_stage_mapping_id
        if dto.performed_remark is not None:
            entity.performed_remark = dto.performed_remark
        if dto.approved_remark is not None:
            entity.approved_remark = dto.approved_remark
        if dto.is_self_verified is not None:
            entity.is_self_verified = dto.is_self_verified
        if dto.self_verification_details is not None:
            entity.self_verification_details = dto.self_verification_details
        if dto.is_approvable is not None:
            entity.is_approvable = dto.is_approvable
        if dto.is_last_stage is not None:
            entity.is_last_stage = dto.is_last_stage
        if dto.submit_remarks is not None:
            entity.submit_remarks = dto.submit_remarks
        if dto.self_approved_remark is not None:
            entity.self_approved_remark = dto.self_approved_remark
        entity.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(entity))

    async def delete_stage(self, stage_id: int) -> None:
        await self._require(stage_id)
        await self._repo.delete(stage_id)

    async def _require(self, stage_id: int) -> ChecklistStage:
        entity = await self._repo.get_by_id(stage_id)
        if entity is None:
            raise EntityNotFoundError(ENTITY, stage_id)
        return entity

    @staticmethod
    def _to_dto(e: ChecklistStage) -> ChecklistStageDTO:
        return ChecklistStageDTO(
            id=e.id,
            checklist_request_id=e.checklist_request_id,
            user_id=e.user_id,
            format_stage_mapping_id=e.format_stage_mapping_id,
            status=e.status,
            performed_remark=e.performed_remark,
            approved_remark=e.approved_remark,
            is_self_verified=e.is_self_verified,
            self_verification_details=e.self_verification_details,
            is_approvable=e.is_approvable,
            is_last_stage=e.is_last_stage,
            submit_remarks=e.submit_remarks,
            self_approved_remark=e.self_approved_remark,
            created_by=e.created_by,
            created_date=e.created_date,
            modified_by=e.modified_by,
            modified_date=e.modified_date,
        )
