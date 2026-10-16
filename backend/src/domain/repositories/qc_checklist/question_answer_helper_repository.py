"""QuestionAnswerHelper — repository port."""

from abc import abstractmethod

from src.domain.entities.qc_checklist.question_answer_helper import QuestionAnswerHelper
from src.domain.repositories.base_repository import IRepository


class IQuestionAnswerHelperRepository(IRepository[QuestionAnswerHelper]):

    @abstractmethod
    async def list_by_question_answer(self, question_answer_id: int) -> list[QuestionAnswerHelper]:
        """Return all helpers linked to a specific question answer (via junction)."""
        ...

    @abstractmethod
    async def replace_for_answer(
        self, question_answer_id: int, texts: list[str], actor: str
    ) -> None:
        """Replace all helper rows for a question answer: delete the existing
        ones and insert a row per non-blank text. Owns its own flush."""
        ...
