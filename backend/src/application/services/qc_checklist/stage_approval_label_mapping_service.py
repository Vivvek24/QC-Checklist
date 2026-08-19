"""StageApprovalLabelMapping — application service."""

from src.application.dtos.qc_checklist.stage_approval_label_mapping_dtos import (
    CreateStageApprovalLabelMappingDTO,
    StageApprovalLabelMappingDTO,
    StageApprovalLabelMappingListDTO,
    UpdateStageApprovalLabelMappingDTO,
)
from src.domain.entities.qc_checklist.stage_approval_label_mapping import StageApprovalLabelMapping
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.domain.repositories.qc_checklist.stage_approval_label_mapping_repository import IStageApprovalLabelMappingRepository

ENTITY = "StageApprovalLabelMapping"


class StageApprovalLabelMappingService:
    def __init__(self, repo: IStageApprovalLabelMappingRepository) -> None:
        self._repo = repo

    async def list_mappings(self, skip: int = 0, limit: int = 100) -> StageApprovalLabelMappingListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit)
        total = await self._repo.count()
        return StageApprovalLabelMappingListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[StageApprovalLabelMappingDTO]:
        items = await self._repo.list_by_checklist_stage(checklist_stage_id)
        return [self._to_dto(i) for i in items]

    async def list_by_approval_label(self, approval_label_id: int) -> list[StageApprovalLabelMappingDTO]:
        items = await self._repo.list_by_approval_label(approval_label_id)
        return [self._to_dto(i) for i in items]

    async def get_mapping(self, mapping_id: int) -> StageApprovalLabelMappingDTO:
        return self._to_dto(await self._require(mapping_id))

    async def create_mapping(self, dto: CreateStageApprovalLabelMappingDTO, actor: User) -> StageApprovalLabelMappingDTO:
        created = await self._repo.create(StageApprovalLabelMapping(
            checklist_stage_id=dto.checklist_stage_id,
            approval_label_id=dto.approval_label_id,
            remark_id=dto.remark_id,
            user_id=dto.user_id,
            role_id=dto.role_id,
            date_of_action=dto.date_of_action,
            remark=dto.remark,
            is_show=dto.is_show,
            is_refer_back=dto.is_refer_back,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_mapping(self, mapping_id: int, dto: UpdateStageApprovalLabelMappingDTO, actor: User) -> StageApprovalLabelMappingDTO:
        entity = await self._require(mapping_id)
        if dto.approval_label_id is not None:
            entity.approval_label_id = dto.approval_label_id
        if dto.remark_id is not None:
            entity.remark_id = dto.remark_id
        if dto.user_id is not None:
            entity.user_id = dto.user_id
        if dto.role_id is not None:
            entity.role_id = dto.role_id
        if dto.date_of_action is not None:
            entity.date_of_action = dto.date_of_action
        if dto.remark is not None:
            entity.remark = dto.remark
        if dto.is_show is not None:
            entity.is_show = dto.is_show
        if dto.is_refer_back is not None:
            entity.is_refer_back = dto.is_refer_back
        entity.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(entity))

    async def delete_mapping(self, mapping_id: int) -> None:
        await self._require(mapping_id)
        await self._repo.delete(mapping_id)

    async def _require(self, mapping_id: int) -> StageApprovalLabelMapping:
        entity = await self._repo.get_by_id(mapping_id)
        if entity is None:
            raise EntityNotFoundError(ENTITY, mapping_id)
        return entity

    @staticmethod
    def _to_dto(e: StageApprovalLabelMapping) -> StageApprovalLabelMappingDTO:
        return StageApprovalLabelMappingDTO(
            id=e.id,
            checklist_stage_id=e.checklist_stage_id,
            approval_label_id=e.approval_label_id,
            remark_id=e.remark_id,
            user_id=e.user_id,
            role_id=e.role_id,
            date_of_action=e.date_of_action,
            remark=e.remark,
            is_show=e.is_show,
            is_refer_back=e.is_refer_back,
            created_by=e.created_by,
            created_date=e.created_date,
            modified_by=e.modified_by,
            modified_date=e.modified_date,
        )
