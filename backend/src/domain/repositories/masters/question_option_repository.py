"""QuestionOption Master — repository port."""

from abc import abstractmethod

from src.domain.entities.masters.question_option import QuestionOption
from src.domain.repositories.base_repository import IRepository


class IQuestionOptionRepository(IRepository[QuestionOption]):

    @abstractmethod
    async def exists_by_title_for_question(
        self, option_title: str, question_id: int, exclude_id: int | None = None
    ) -> bool:
        """Check whether an option title already exists for a given question."""
        ...

    @abstractmethod
    async def list_by_question(self, question_id: int) -> list[QuestionOption]:
        """Return all options for a specific question."""
        ...
