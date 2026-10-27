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
    async def list_by_stage_question_mapping(
        self, stage_question_mapping_id: int
    ) -> list[QuestionAnswer]:
        """Return all answers for a specific stage question mapping."""
        ...

    @abstractmethod
    async def delete_sub_answers_by_parent(self, parent_question_answer_id: int) -> None:
        """Remove a parent answer's sub-question child answers and their links."""
        ...

    @abstractmethod
    async def link_sub_answer(
        self, parent_question_answer_id: int, child_question_answer_id: int, actor: str
    ) -> None:
        """Link a child answer to its parent via the sub-question self-join."""
        ...

    @abstractmethod
    async def list_sub_answers_grouped(
        self, checklist_stage_id: int
    ) -> dict[int, list[tuple[int, int | None, int | None, str, str]]]:
        """For each parent answer in the stage, return its child sub-answers
        keyed by the parent's question_id. Each child tuple is
        (question_id, question_option_id, response_question_option_id,
        textbox_value, response_answer)."""
        ...

    @abstractmethod
    async def resolve_user_names(self, user_ids: set[int]) -> dict[int, str]:
        """Map user ids → full name (user_details.employee_name, falling back
        to username). Used to show the receiving analyst on issued rows."""
        ...

    @abstractmethod
    async def list_helpers_by_answer_ids(
        self, answer_ids: list[int]
    ) -> dict[int, list[str]]:
        """Map answer id → its ordered "+ Add" helper text values."""
        ...
