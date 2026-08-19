"""ChecklistRequest — application service."""

from src.application.dtos.qc_checklist.checklist_request_dtos import (
    ChecklistRequestDTO,
    ChecklistRequestListDTO,
    CreateChecklistRequestDTO,
    UpdateChecklistRequestDTO,
)
from src.domain.entities.qc_checklist.checklist_request import ChecklistRequest
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.qc_checklist.checklist_request_repository import IChecklistRequestRepository

ENTITY = "ChecklistRequest"


class ChecklistRequestService:
    def __init__(self, repo: IChecklistRequestRepository) -> None:
        self._repo = repo

    async def list_requests(
        self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None
    ) -> ChecklistRequestListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        total = await self._repo.count(search=search, is_active=is_active)
        return ChecklistRequestListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def get_request(self, request_id: int) -> ChecklistRequestDTO:
        return self._to_dto(await self._require(request_id))

    async def create_request(self, dto: CreateChecklistRequestDTO, actor: User) -> ChecklistRequestDTO:
        if await self._repo.exists_by_request_number(dto.request_number):
            raise DuplicateEntityError(ENTITY, "request_number", dto.request_number)
        seq = await self._repo.get_next_sequence_number()
        created = await self._repo.create(ChecklistRequest(
            status=dto.status,
            request_number=dto.request_number,
            status_format=dto.status_format,
            is_last_stage=dto.is_last_stage,
            is_removed=dto.is_removed,
            sequence_number=seq,
            approver_user_id=dto.approver_user_id,
            format_id=dto.format_id,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_request(self, request_id: int, dto: UpdateChecklistRequestDTO, actor: User) -> ChecklistRequestDTO:
        entity = await self._require(request_id)
        if dto.request_number is not None and dto.request_number != entity.request_number:
            if await self._repo.exists_by_request_number(dto.request_number, exclude_id=request_id):
                raise DuplicateEntityError(ENTITY, "request_number", dto.request_number)
            entity.request_number = dto.request_number
        if dto.status is not None:
            entity.status = dto.status
        if dto.status_format is not None:
            entity.status_format = dto.status_format
        if dto.is_last_stage is not None:
            entity.is_last_stage = dto.is_last_stage
        if dto.is_removed is not None:
            entity.is_removed = dto.is_removed
        if dto.approver_user_id is not None:
            entity.approver_user_id = dto.approver_user_id
        if dto.format_id is not None:
            entity.format_id = dto.format_id
        entity.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(entity))

    async def delete_request(self, request_id: int) -> None:
        await self._require(request_id)
        await self._repo.delete(request_id)

    async def _require(self, request_id: int) -> ChecklistRequest:
        entity = await self._repo.get_by_id(request_id)
        if entity is None:
            raise EntityNotFoundError(ENTITY, request_id)
        return entity

    @staticmethod
    def _to_dto(e: ChecklistRequest) -> ChecklistRequestDTO:
        return ChecklistRequestDTO(
            id=e.id,
            status=e.status,
            request_number=e.request_number,
            status_format=e.status_format,
            is_last_stage=e.is_last_stage,
            is_removed=e.is_removed,
            sequence_number=e.sequence_number,
            approver_user_id=e.approver_user_id,
            format_id=e.format_id,
            created_by=e.created_by,
            created_date=e.created_date,
            modified_by=e.modified_by,
            modified_date=e.modified_date,
        )
