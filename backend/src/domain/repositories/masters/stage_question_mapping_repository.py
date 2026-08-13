"""StageQuestionMapping — repository port."""

from abc import abstractmethod

from src.domain.entities.masters.stage_question_mapping import StageQuestionMapping
from src.domain.repositories.base_repository import IRepository


class IStageQuestionMappingRepository(IRepository[StageQuestionMapping]):

    @abstractmethod
    async def exists_by_mapping_and_question(
        self, format_stage_mapping_id: int, question_id: int, exclude_id: int | None = None
    ) -> bool:
        """Check whether a question is already mapped to a format-stage mapping."""
        ...

    @abstractmethod
    async def list_by_format_stage_mapping(self, format_stage_mapping_id: int) -> list[StageQuestionMapping]:
        """Return all question mappings for a specific format-stage mapping."""
        ...
