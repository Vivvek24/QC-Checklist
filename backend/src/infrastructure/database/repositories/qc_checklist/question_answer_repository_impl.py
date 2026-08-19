"""QuestionAnswer — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.qc_checklist.question_answer import QuestionAnswer
from src.domain.repositories.qc_checklist.question_answer_repository import IQuestionAnswerRepository
from src.infrastructure.database.models.qc_checklist.question_answer_model import QuestionAnswerModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class QuestionAnswerRepositoryImpl(SqlAlchemyRepository[QuestionAnswer, QuestionAnswerModel], IQuestionAnswerRepository):
    _model = QuestionAnswerModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return QuestionAnswerModel.id == -1

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[QuestionAnswer]:
        stmt = select(QuestionAnswerModel).order_by(QuestionAnswerModel.id.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = select(func.count()).select_from(QuestionAnswerModel)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return False

    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[QuestionAnswer]:
        stmt = select(QuestionAnswerModel).where(
            QuestionAnswerModel.checklist_stage_id == checklist_stage_id
        ).order_by(QuestionAnswerModel.serial_number)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_stage_question_mapping(self, stage_question_mapping_id: int) -> list[QuestionAnswer]:
        stmt = select(QuestionAnswerModel).where(
            QuestionAnswerModel.stage_question_mapping_id == stage_question_mapping_id
        ).order_by(QuestionAnswerModel.serial_number)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: QuestionAnswer) -> QuestionAnswer:
        model = QuestionAnswerModel(
            checklist_stage_id=entity.checklist_stage_id,
            checklist_stage_section_id=entity.checklist_stage_section_id,
            product_id=entity.product_id,
            question_id=entity.question_id,
            question_option_id=entity.question_option_id,
            receiver_user_id=entity.receiver_user_id,
            response_question_option_id=entity.response_question_option_id,
            stage_question_mapping_id=entity.stage_question_mapping_id,
            textbox_value=entity.textbox_value,
            response_answer=entity.response_answer,
            comma_separated_name=entity.comma_separated_name,
            has_helper=entity.has_helper,
            serial_number=entity.serial_number,
            sub_answer_serial_no=entity.sub_answer_serial_no,
            date_time=entity.date_time,
            test_title=entity.test_title,
            sample_vails=entity.sample_vails,
            answer_total_vails=entity.answer_total_vails,
            issued_by_date=entity.issued_by_date,
            received_by_date=entity.received_by_date,
            issuer_name=entity.issuer_name,
            is_issued_vails=entity.is_issued_vails,
            has_vails=entity.has_vails,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: QuestionAnswer) -> QuestionAnswer:
        model = await self._require_model(entity.id)
        model.checklist_stage_id = entity.checklist_stage_id
        model.checklist_stage_section_id = entity.checklist_stage_section_id
        model.product_id = entity.product_id
        model.question_id = entity.question_id
        model.question_option_id = entity.question_option_id
        model.receiver_user_id = entity.receiver_user_id
        model.response_question_option_id = entity.response_question_option_id
        model.stage_question_mapping_id = entity.stage_question_mapping_id
        model.textbox_value = entity.textbox_value
        model.response_answer = entity.response_answer
        model.comma_separated_name = entity.comma_separated_name
        model.has_helper = entity.has_helper
        model.serial_number = entity.serial_number
        model.sub_answer_serial_no = entity.sub_answer_serial_no
        model.date_time = entity.date_time
        model.test_title = entity.test_title
        model.sample_vails = entity.sample_vails
        model.answer_total_vails = entity.answer_total_vails
        model.issued_by_date = entity.issued_by_date
        model.received_by_date = entity.received_by_date
        model.issuer_name = entity.issuer_name
        model.is_issued_vails = entity.is_issued_vails
        model.has_vails = entity.has_vails
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: QuestionAnswerModel) -> QuestionAnswer:
        return QuestionAnswer(
            id=model.id,
            checklist_stage_id=model.checklist_stage_id,
            checklist_stage_section_id=model.checklist_stage_section_id,
            product_id=model.product_id,
            question_id=model.question_id,
            question_option_id=model.question_option_id,
            receiver_user_id=model.receiver_user_id,
            response_question_option_id=model.response_question_option_id,
            stage_question_mapping_id=model.stage_question_mapping_id,
            textbox_value=model.textbox_value,
            response_answer=model.response_answer,
            comma_separated_name=model.comma_separated_name,
            has_helper=model.has_helper,
            serial_number=model.serial_number,
            sub_answer_serial_no=model.sub_answer_serial_no,
            date_time=model.date_time,
            test_title=model.test_title,
            sample_vails=model.sample_vails,
            answer_total_vails=model.answer_total_vails,
            issued_by_date=model.issued_by_date,
            received_by_date=model.received_by_date,
            issuer_name=model.issuer_name,
            is_issued_vails=model.is_issued_vails,
            has_vails=model.has_vails,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
