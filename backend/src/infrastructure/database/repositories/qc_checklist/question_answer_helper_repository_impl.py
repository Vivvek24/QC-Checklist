"""QuestionAnswerHelper — repository implementation."""

from sqlalchemy import ColumnElement, func, select

from src.domain.entities.qc_checklist.question_answer_helper import QuestionAnswerHelper
from src.domain.repositories.qc_checklist.question_answer_helper_repository import IQuestionAnswerHelperRepository
from src.infrastructure.database.models.qc_checklist.question_answer_helper_model import QuestionAnswerHelperModel
from src.infrastructure.database.models.qc_checklist.question_answer_sub_question_answer_model import QuestionAnswerSubQuestionAnswerModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class QuestionAnswerHelperRepositoryImpl(SqlAlchemyRepository[QuestionAnswerHelper, QuestionAnswerHelperModel], IQuestionAnswerHelperRepository):
    _model = QuestionAnswerHelperModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return QuestionAnswerHelperModel.id == -1

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[QuestionAnswerHelper]:
        stmt = select(QuestionAnswerHelperModel).order_by(QuestionAnswerHelperModel.id.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = select(func.count()).select_from(QuestionAnswerHelperModel)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return False

    async def list_by_question_answer(self, question_answer_id: int) -> list[QuestionAnswerHelper]:
        stmt = (
            select(QuestionAnswerHelperModel)
            .join(
                QuestionAnswerSubQuestionAnswerModel,
                QuestionAnswerSubQuestionAnswerModel.question_answer_helper_id == QuestionAnswerHelperModel.id,
            )
            .where(QuestionAnswerSubQuestionAnswerModel.question_answer_id == question_answer_id)
            .order_by(QuestionAnswerHelperModel.id)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: QuestionAnswerHelper) -> QuestionAnswerHelper:
        model = QuestionAnswerHelperModel(
            text_box_value=entity.text_box_value,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: QuestionAnswerHelper) -> QuestionAnswerHelper:
        model = await self._require_model(entity.id)
        model.text_box_value = entity.text_box_value
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    async def link_to_question_answer(self, question_answer_id: int, helper_id: int, created_by: str) -> None:
        """Create junction record linking a helper to a question answer."""
        junction = QuestionAnswerSubQuestionAnswerModel(
            question_answer_id=question_answer_id,
            question_answer_helper_id=helper_id,
            created_by=created_by,
            modified_by=created_by,
        )
        self._session.add(junction)
        await self._session.flush()

    async def unlink_from_question_answer(self, question_answer_id: int, helper_id: int) -> None:
        """Remove junction record."""
        stmt = select(QuestionAnswerSubQuestionAnswerModel).where(
            QuestionAnswerSubQuestionAnswerModel.question_answer_id == question_answer_id,
            QuestionAnswerSubQuestionAnswerModel.question_answer_helper_id == helper_id,
        )
        result = await self._session.execute(stmt)
        junction = result.scalar_one_or_none()
        if junction:
            await self._session.delete(junction)
            await self._session.flush()

    @staticmethod
    def _to_entity(model: QuestionAnswerHelperModel) -> QuestionAnswerHelper:
        return QuestionAnswerHelper(
            id=model.id,
            text_box_value=model.text_box_value,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
