from src.application.dtos.masters.approval_label_dtos import *
from src.domain.entities.masters.approval_label import ApprovalLabel
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.approval_label_repository import IApprovalLabelRepository
ENTITY = "ApprovalLabel"

class ApprovalLabelService:
    def __init__(self, repo: IApprovalLabelRepository) -> None: self._repo = repo

    async def list_all(self, skip=0, limit=100, search=None, is_active=None, stage_id=None, question_id=None) -> ApprovalLabelListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active, stage_id=stage_id, question_id=question_id)
        return ApprovalLabelListDTO(items=[self._d(i) for i in items], total=await self._repo.count(search=search, is_active=is_active, stage_id=stage_id, question_id=question_id), skip=skip, limit=limit)

    async def get(self, id: int) -> ApprovalLabelDTO: return self._d(await self._req(id))

    async def create(self, dto: CreateApprovalLabelDTO, actor: User) -> ApprovalLabelDTO:
        await self._check_duplicate(dto.label, dto.stage_id, dto.question_id)
        return self._d(await self._repo.create(ApprovalLabel(label=dto.label.strip(), stage_id=dto.stage_id, question_id=dto.question_id, role_ids=dto.role_ids, is_active=dto.is_active, created_by=actor.username, modified_by=actor.username)))

    async def update(self, id: int, dto: UpdateApprovalLabelDTO, actor: User) -> ApprovalLabelDTO:
        e = await self._req(id)
        stage_id = dto.stage_id if dto.stage_id is not None else e.stage_id
        question_id = dto.question_id if dto.question_id is not None else e.question_id
        if dto.label and dto.label.strip() != e.label:
            await self._check_duplicate(dto.label, stage_id, question_id, exclude_id=id)
            e.label = dto.label.strip()
        if dto.stage_id is not None: e.stage_id = dto.stage_id
        if dto.question_id is not None: e.question_id = dto.question_id
        if dto.role_ids is not None: e.role_ids = dto.role_ids
        if dto.is_active is not None: e.is_active = dto.is_active
        e.mark_modified(actor.username)
        return self._d(await self._repo.update(e))

    async def _check_duplicate(self, label: str, stage_id: int | None, question_id: int | None, exclude_id: int | None = None) -> None:
        """A label must be unique within its owner (its stage, or its question)."""
        if question_id is not None:
            if await self._repo.exists_by_label_for_question(label, question_id, exclude_id=exclude_id):
                raise DuplicateEntityError(ENTITY, "label", label)
        elif stage_id is not None:
            if await self._repo.exists_by_label_for_stage(label, stage_id, exclude_id=exclude_id):
                raise DuplicateEntityError(ENTITY, "label", label)

    async def delete(self, id: int) -> None: await self._req(id); await self._repo.delete(id)

    async def _req(self, id: int) -> ApprovalLabel:
        e = await self._repo.get_by_id(id)
        if not e: raise EntityNotFoundError(ENTITY, id)
        return e

    @staticmethod
    def _d(e: ApprovalLabel) -> ApprovalLabelDTO:
        return ApprovalLabelDTO(id=e.id, label=e.label, stage_id=e.stage_id, question_id=e.question_id, role_ids=e.role_ids, is_active=e.is_active,
                                created_by=e.created_by, created_date=e.created_date, modified_by=e.modified_by, modified_date=e.modified_date)
