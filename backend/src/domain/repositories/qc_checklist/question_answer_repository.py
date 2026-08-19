"""QuestionAnswer — repository port."""

from abc import abstractmethod

from src.domain.entities.qc_checklist.question_answer import QuestionAnswer
from src.domain.repositories.base_repository import IRepository


class IQuestionAnswerRepository(IRepository[QuestionAnswer]):

    @abstractmethod
    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[QuestionAnswer]:
        """Return all answers for a specific checklist stage."""
        ...

    @abstractmethod
    async def list_by_stage_question_mapping(self, stage_question_mapping_id: int) -> list[QuestionAnswer]:
        """Return all answers for a specific stage question mapping."""
        ...
