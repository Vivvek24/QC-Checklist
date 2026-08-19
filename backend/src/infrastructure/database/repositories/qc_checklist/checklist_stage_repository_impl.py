"""ChecklistStage — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.qc_checklist.checklist_stage import ChecklistStage
from src.domain.repositories.qc_checklist.checklist_stage_repository import IChecklistStageRepository
from src.infrastructure.database.models.qc_checklist.checklist_stage_model import ChecklistStageModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class ChecklistStageRepositoryImpl(SqlAlchemyRepository[ChecklistStage, ChecklistStageModel], IChecklistStageRepository):
    _model = ChecklistStageModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return ChecklistStageModel.id == -1

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[ChecklistStage]:
        stmt = self._apply_filters(select(ChecklistStageModel), search, is_active)
        stmt = stmt.order_by(ChecklistStageModel.id.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = self._apply_filters(select(func.count()).select_from(ChecklistStageModel), search, is_active)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return False

    async def list_by_checklist_request(self, checklist_request_id: int) -> list[ChecklistStage]:
        stmt = select(ChecklistStageModel).where(
            ChecklistStageModel.checklist_request_id == checklist_request_id
        ).order_by(ChecklistStageModel.id)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: ChecklistStage) -> ChecklistStage:
        model = ChecklistStageModel(
            checklist_request_id=entity.checklist_request_id,
            user_id=entity.user_id,
            format_stage_mapping_id=entity.format_stage_mapping_id,
            status=entity.status,
            performed_remark=entity.performed_remark,
            approved_remark=entity.approved_remark,
            is_self_verified=entity.is_self_verified,
            self_verification_details=entity.self_verification_details,
            is_approvable=entity.is_approvable,
            is_last_stage=entity.is_last_stage,
            submit_remarks=entity.submit_remarks,
            self_approved_remark=entity.self_approved_remark,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: ChecklistStage) -> ChecklistStage:
        model = await self._require_model(entity.id)
        model.checklist_request_id = entity.checklist_request_id
        model.user_id = entity.user_id
        model.format_stage_mapping_id = entity.format_stage_mapping_id
        model.status = entity.status
        model.performed_remark = entity.performed_remark
        model.approved_remark = entity.approved_remark
        model.is_self_verified = entity.is_self_verified
        model.self_verification_details = entity.self_verification_details
        model.is_approvable = entity.is_approvable
        model.is_last_stage = entity.is_last_stage
        model.submit_remarks = entity.submit_remarks
        model.self_approved_remark = entity.self_approved_remark
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search:
            stmt = stmt.where(ChecklistStageModel.status.ilike(f"%{search}%"))
        return stmt

    @staticmethod
    def _to_entity(model: ChecklistStageModel) -> ChecklistStage:
        return ChecklistStage(
            id=model.id,
            checklist_request_id=model.checklist_request_id,
            user_id=model.user_id,
            format_stage_mapping_id=model.format_stage_mapping_id,
            status=model.status,
            performed_remark=model.performed_remark,
            approved_remark=model.approved_remark,
            is_self_verified=model.is_self_verified,
            self_verification_details=model.self_verification_details,
            is_approvable=model.is_approvable,
            is_last_stage=model.is_last_stage,
            submit_remarks=model.submit_remarks,
            self_approved_remark=model.self_approved_remark,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
