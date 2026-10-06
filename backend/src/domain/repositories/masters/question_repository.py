"""Question Master — repository port."""

from abc import abstractmethod

from src.domain.entities.masters.question import Question
from src.domain.repositories.base_repository import IRepository


class IQuestionRepository(IRepository[Question]):

    @abstractmethod
    async def exists_by_title(self, title: str, exclude_id: int | None = None) -> bool:
        """Check whether a question title is already taken."""
        ...

    @abstractmethod
    async def list_by_ids(self, question_ids: list[int]) -> list[Question]:
        """Bulk-load questions by id. Returns only the ones that exist."""
        ...
