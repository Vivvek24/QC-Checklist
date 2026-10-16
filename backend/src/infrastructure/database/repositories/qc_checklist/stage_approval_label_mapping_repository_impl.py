"""StageApprovalLabelMapping — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.qc_checklist.stage_approval_label_mapping import StageApprovalLabelMapping
from src.domain.repositories.qc_checklist.stage_approval_label_mapping_repository import IStageApprovalLabelMappingRepository
from src.infrastructure.database.models.qc_checklist.stage_approval_label_mapping_model import StageApprovalLabelMappingModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class StageApprovalLabelMappingRepositoryImpl(SqlAlchemyRepository[StageApprovalLabelMapping, StageApprovalLabelMappingModel], IStageApprovalLabelMappingRepository):
    _model = StageApprovalLabelMappingModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return StageApprovalLabelMappingModel.id == -1

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[StageApprovalLabelMapping]:
        stmt = select(StageApprovalLabelMappingModel).order_by(StageApprovalLabelMappingModel.id.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = select(func.count()).select_from(StageApprovalLabelMappingModel)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return False

    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[StageApprovalLabelMapping]:
        stmt = select(StageApprovalLabelMappingModel).where(
            StageApprovalLabelMappingModel.checklist_stage_id == checklist_stage_id
        ).order_by(StageApprovalLabelMappingModel.id)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_checklist_request(self, checklist_request_id: int) -> list[StageApprovalLabelMapping]:
        """All per-question approval mappings for a request — joins each
        mapping's question_answer up to its stage's checklist_request_id."""
        from src.infrastructure.database.models.qc_checklist.checklist_stage_model import (
            ChecklistStageModel,
        )
        from src.infrastructure.database.models.qc_checklist.question_answer_model import (
            QuestionAnswerModel,
        )
        stmt = (
            select(StageApprovalLabelMappingModel)
            .join(
                QuestionAnswerModel,
                QuestionAnswerModel.id == StageApprovalLabelMappingModel.question_answer_id,
            )
            .join(
                ChecklistStageModel,
                ChecklistStageModel.id == QuestionAnswerModel.checklist_stage_id,
            )
            .where(ChecklistStageModel.checklist_request_id == checklist_request_id)
            .order_by(StageApprovalLabelMappingModel.id)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_question_answer(self, question_answer_id: int) -> list[StageApprovalLabelMapping]:
        stmt = select(StageApprovalLabelMappingModel).where(
            StageApprovalLabelMappingModel.question_answer_id == question_answer_id
        ).order_by(StageApprovalLabelMappingModel.id)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_question_answers(self, question_answer_ids: list[int]) -> list[StageApprovalLabelMapping]:
        if not question_answer_ids:
            return []
        stmt = select(StageApprovalLabelMappingModel).where(
            StageApprovalLabelMappingModel.question_answer_id.in_(question_answer_ids)
        ).order_by(StageApprovalLabelMappingModel.id)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_approval_label(self, approval_label_id: int) -> list[StageApprovalLabelMapping]:
        stmt = select(StageApprovalLabelMappingModel).where(
            StageApprovalLabelMappingModel.approval_label_id == approval_label_id
        ).order_by(StageApprovalLabelMappingModel.id)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: StageApprovalLabelMapping) -> StageApprovalLabelMapping:
        model = StageApprovalLabelMappingModel(
            checklist_stage_id=entity.checklist_stage_id,
            question_answer_id=entity.question_answer_id,
            approval_label_id=entity.approval_label_id,
            remark_id=entity.remark_id,
            user_id=entity.user_id,
            role_id=entity.role_id,
            date_of_action=entity.date_of_action,
            remark=entity.remark,
            is_show=entity.is_show,
            is_refer_back=entity.is_refer_back,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: StageApprovalLabelMapping) -> StageApprovalLabelMapping:
        model = await self._require_model(entity.id)
        model.checklist_stage_id = entity.checklist_stage_id
        model.question_answer_id = entity.question_answer_id
        model.approval_label_id = entity.approval_label_id
        model.remark_id = entity.remark_id
        model.user_id = entity.user_id
        model.role_id = entity.role_id
        model.date_of_action = entity.date_of_action
        model.remark = entity.remark
        model.is_show = entity.is_show
        model.is_refer_back = entity.is_refer_back
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: StageApprovalLabelMappingModel) -> StageApprovalLabelMapping:
        return StageApprovalLabelMapping(
            id=model.id,
            checklist_stage_id=model.checklist_stage_id,
            question_answer_id=model.question_answer_id,
            approval_label_id=model.approval_label_id,
            remark_id=model.remark_id,
            user_id=model.user_id,
            role_id=model.role_id,
            date_of_action=model.date_of_action,
            remark=model.remark,
            is_show=model.is_show,
            is_refer_back=model.is_refer_back,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
