"""Question Master — repository port."""

from abc import abstractmethod

from src.domain.entities.masters.question import Question
from src.domain.repositories.base_repository import IRepository


class IQuestionRepository(IRepository[Question]):

    @abstractmethod
    async def exists_by_title(self, title: str, exclude_id: int | None = None) -> bool:
        """Check whether a question title is already taken."""
        ...
