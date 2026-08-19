"""ChecklistRequest — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.qc_checklist.checklist_request import ChecklistRequest
from src.domain.repositories.qc_checklist.checklist_request_repository import IChecklistRequestRepository
from src.infrastructure.database.models.qc_checklist.checklist_request_model import ChecklistRequestModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class ChecklistRequestRepositoryImpl(SqlAlchemyRepository[ChecklistRequest, ChecklistRequestModel], IChecklistRequestRepository):
    _model = ChecklistRequestModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return ChecklistRequestModel.request_number == code

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[ChecklistRequest]:
        stmt = self._apply_filters(select(ChecklistRequestModel), search, is_active)
        stmt = stmt.order_by(ChecklistRequestModel.id.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = self._apply_filters(select(func.count()).select_from(ChecklistRequestModel), search, is_active)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_request_number(code, exclude_id)

    async def exists_by_request_number(self, request_number: str, exclude_id: int | None = None) -> bool:
        stmt = select(ChecklistRequestModel.id).where(
            ChecklistRequestModel.request_number == request_number
        )
        if exclude_id is not None:
            stmt = stmt.where(ChecklistRequestModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_next_sequence_number(self) -> int:
        stmt = select(func.coalesce(func.max(ChecklistRequestModel.sequence_number), 0))
        result = await self._session.execute(stmt)
        return int(result.scalar_one()) + 1

    async def create(self, entity: ChecklistRequest) -> ChecklistRequest:
        model = ChecklistRequestModel(
            status=entity.status,
            request_number=entity.request_number,
            status_format=entity.status_format,
            is_last_stage=entity.is_last_stage,
            is_removed=entity.is_removed,
            sequence_number=entity.sequence_number,
            approver_user_id=entity.approver_user_id,
            format_id=entity.format_id,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: ChecklistRequest) -> ChecklistRequest:
        model = await self._require_model(entity.id)
        model.status = entity.status
        model.request_number = entity.request_number
        model.status_format = entity.status_format
        model.is_last_stage = entity.is_last_stage
        model.is_removed = entity.is_removed
        model.sequence_number = entity.sequence_number
        model.approver_user_id = entity.approver_user_id
        model.format_id = entity.format_id
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search:
            stmt = stmt.where(ChecklistRequestModel.request_number.ilike(f"%{search}%"))
        if is_active is not None:
            stmt = stmt.where(ChecklistRequestModel.is_removed.is_(not is_active))
        return stmt

    @staticmethod
    def _to_entity(model: ChecklistRequestModel) -> ChecklistRequest:
        return ChecklistRequest(
            id=model.id,
            status=model.status,
            request_number=model.request_number,
            status_format=model.status_format,
            is_last_stage=model.is_last_stage,
            is_removed=model.is_removed,
            sequence_number=model.sequence_number,
            approver_user_id=model.approver_user_id,
            format_id=model.format_id,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
