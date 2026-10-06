"""QuestionSubQuestion — repository implementation (read-only adapter)."""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.masters.question_sub_question_repository import (
    IQuestionSubQuestionRepository,
)
from src.infrastructure.database.models.masters.question_model import QuestionSubQuestionModel


class QuestionSubQuestionRepositoryImpl(IQuestionSubQuestionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_sub_question_ids_by_parents(
        self, question_ids: list[int]
    ) -> dict[int, list[int]]:
        if not question_ids:
            return {}
        stmt = select(
            QuestionSubQuestionModel.question_id, QuestionSubQuestionModel.sub_question_id
        ).where(QuestionSubQuestionModel.question_id.in_(question_ids))
        result = await self._session.execute(stmt)
        by_parent: dict[int, list[int]] = defaultdict(list)
        for question_id, sub_question_id in result.all():
            by_parent[question_id].append(sub_question_id)
        return dict(by_parent)
