"""QuestionOption Master — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.masters.question_option import QuestionOption
from src.domain.repositories.masters.question_option_repository import IQuestionOptionRepository
from src.infrastructure.database.models.masters.question_option_model import QuestionOptionModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class QuestionOptionRepositoryImpl(SqlAlchemyRepository[QuestionOption, QuestionOptionModel], IQuestionOptionRepository):
    _model = QuestionOptionModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(QuestionOptionModel.option_title) == code.lower()

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[QuestionOption]:
        stmt = self._apply_filters(select(QuestionOptionModel), search, is_active)
        stmt = stmt.order_by(QuestionOptionModel.option_title).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = self._apply_filters(select(func.count()).select_from(QuestionOptionModel), search, is_active)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_by_question(self, question_id: int) -> list[QuestionOption]:
        stmt = select(QuestionOptionModel).where(
            QuestionOptionModel.question_id == question_id
        ).order_by(QuestionOptionModel.option_title)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_title_for_question(code, 0, exclude_id)

    async def exists_by_title_for_question(
        self, option_title: str, question_id: int, exclude_id: int | None = None
    ) -> bool:
        stmt = select(QuestionOptionModel.id).where(
            func.lower(QuestionOptionModel.option_title) == option_title.lower(),
            QuestionOptionModel.question_id == question_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(QuestionOptionModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, entity: QuestionOption) -> QuestionOption:
        model = QuestionOptionModel(
            option_title=entity.option_title,
            is_response_option=entity.is_response_option,
            question_id=entity.question_id,
            is_active=entity.is_active,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: QuestionOption) -> QuestionOption:
        model = await self._require_model(entity.id)
        model.option_title = entity.option_title
        model.is_response_option = entity.is_response_option
        model.question_id = entity.question_id
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search:
            stmt = stmt.where(QuestionOptionModel.option_title.ilike(f"%{search.strip()}%"))
        if is_active is not None:
            stmt = stmt.where(QuestionOptionModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(model: QuestionOptionModel) -> QuestionOption:
        return QuestionOption(
            id=model.id,
            option_title=model.option_title,
            is_response_option=model.is_response_option,
            question_id=model.question_id,
            is_active=model.is_active,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
