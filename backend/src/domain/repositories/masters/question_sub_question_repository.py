"""QuestionSubQuestion — repository port.

Read-side contract for the question_sub_questions junction table (question
<-> sub-question, many-to-many self-join on Question). Writes to this
junction are owned by QuestionRepositoryImpl (a question's sub-questions are
set as part of saving that question); this port exists for read-only lookups
needed elsewhere, e.g. building a checklist preview.
"""

from abc import ABC, abstractmethod


class IQuestionSubQuestionRepository(ABC):
    """Persistence contract for read access to the question_sub_questions junction."""

    @abstractmethod
    async def list_sub_question_ids_by_parents(
        self, question_ids: list[int]
    ) -> dict[int, list[int]]:
        """Map each parent question_id to its list of sub_question_ids."""
        ...
