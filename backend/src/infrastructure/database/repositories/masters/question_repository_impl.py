"""Question Master — repository implementation with sub-question junction."""

from collections import defaultdict
from typing import Any
from sqlalchemy import ColumnElement, Select, delete, func, select
from src.domain.entities.masters.question import Question
from src.domain.enums.answer_type_enum import AnswerType
from src.domain.enums.master_type_enum import MasterType
from src.domain.repositories.masters.question_repository import IQuestionRepository
from src.infrastructure.database.models.masters.question_model import QuestionModel, QuestionSubQuestionModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class QuestionRepositoryImpl(SqlAlchemyRepository[Question, QuestionModel], IQuestionRepository):
    _model = QuestionModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(QuestionModel.title) == code.lower()

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[Question]:
        stmt = self._apply_filters(select(QuestionModel), search, is_active).order_by(QuestionModel.title).offset(skip).limit(limit)
        models = list((await self._session.execute(stmt)).scalars().all())
        return await self._hydrate(models)

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        return int((await self._session.execute(
            self._apply_filters(select(func.count()).select_from(QuestionModel), search, is_active)
        )).scalar_one())

    async def get_by_id(self, entity_id: int) -> Question | None:
        m = await self._get_model(entity_id)
        if not m: return None
        return (await self._hydrate([m]))[0]

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_title(code, exclude_id)

    async def exists_by_title(self, title: str, exclude_id: int | None = None) -> bool:
        stmt = select(QuestionModel.id).where(func.lower(QuestionModel.title) == title.lower())
        if exclude_id: stmt = stmt.where(QuestionModel.id != exclude_id)
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def create(self, entity: Question) -> Question:
        m = QuestionModel(
            title=entity.title, answer_type=entity.answer_type.value,
            has_text_box=entity.has_text_box, has_multiple_text_box=entity.has_multiple_text_box,
            has_sub_question=entity.has_sub_question, is_validation_required=entity.is_validation_required,
            has_response_option=entity.has_response_option, allow_multiple_input=entity.allow_multiple_input,
            has_associated_master=entity.has_associated_master, is_calculated=entity.is_calculated,
            is_active=entity.is_active, validation_type_id=entity.validation_type_id,
            parent_question_id=entity.parent_question_id,
            master_type=entity.master_type.value if entity.master_type else None,
            created_by=entity.created_by, modified_by=entity.modified_by,
        )
        self._session.add(m); await self._session.flush()
        await self._sync_sub_questions(m.id, entity.sub_question_ids, entity.modified_by)
        return (await self._hydrate([m]))[0]

    async def update(self, entity: Question) -> Question:
        m = await self._require_model(entity.id)
        m.title = entity.title; m.answer_type = entity.answer_type.value
        m.has_text_box = entity.has_text_box; m.has_multiple_text_box = entity.has_multiple_text_box
        m.has_sub_question = entity.has_sub_question; m.is_validation_required = entity.is_validation_required
        m.has_response_option = entity.has_response_option; m.allow_multiple_input = entity.allow_multiple_input
        m.has_associated_master = entity.has_associated_master; m.is_calculated = entity.is_calculated
        m.is_active = entity.is_active; m.validation_type_id = entity.validation_type_id
        m.parent_question_id = entity.parent_question_id
        m.master_type = entity.master_type.value if entity.master_type else None
        m.modified_by = entity.modified_by; m.modified_date = entity.modified_date
        await self._session.flush()
        await self._sync_sub_questions(entity.id, entity.sub_question_ids, entity.modified_by)
        return (await self._hydrate([m]))[0]

    async def _sync_sub_questions(self, question_id: int, sub_ids: list[int], modified_by: str) -> None:
        await self._session.execute(delete(QuestionSubQuestionModel).where(QuestionSubQuestionModel.question_id == question_id))
        for sid in sub_ids:
            self._session.add(QuestionSubQuestionModel(question_id=question_id, sub_question_id=sid, created_by=modified_by, modified_by=modified_by))
        await self._session.flush()

    async def _hydrate(self, models: list[QuestionModel]) -> list[Question]:
        if not models: return []
        ids = [m.id for m in models]
        result = await self._session.execute(
            select(QuestionSubQuestionModel.question_id, QuestionSubQuestionModel.sub_question_id)
            .where(QuestionSubQuestionModel.question_id.in_(ids))
        )
        sub_map: dict[int, list[int]] = defaultdict(list)
        for row in result.all(): sub_map[row[0]].append(row[1])
        return [self._to_entity_full(m, sub_map.get(m.id, [])) for m in models]

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search: stmt = stmt.where(QuestionModel.title.ilike(f"%{search.strip()}%"))
        if is_active is not None: stmt = stmt.where(QuestionModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(m: QuestionModel) -> Question:
        return QuestionRepositoryImpl._to_entity_full(m, [])

    @staticmethod
    def _to_entity_full(m: QuestionModel, sub_ids: list[int]) -> Question:
        return Question(
            id=m.id, title=m.title, answer_type=AnswerType(m.answer_type),
            has_text_box=m.has_text_box, has_multiple_text_box=m.has_multiple_text_box,
            has_sub_question=m.has_sub_question, is_validation_required=m.is_validation_required,
            has_response_option=m.has_response_option, allow_multiple_input=m.allow_multiple_input,
            has_associated_master=m.has_associated_master, is_calculated=m.is_calculated,
            is_active=m.is_active, validation_type_id=m.validation_type_id,
            parent_question_id=m.parent_question_id,
            master_type=MasterType(m.master_type) if m.master_type else None,
            sub_question_ids=sub_ids,
            created_by=m.created_by, created_date=m.created_date,
            modified_by=m.modified_by, modified_date=m.modified_date,
        )
