"""ChecklistStageSection — repository port."""

from abc import abstractmethod

from src.domain.entities.qc_checklist.checklist_stage_section import ChecklistStageSection
from src.domain.repositories.base_repository import IRepository


class IChecklistStageSectionRepository(IRepository[ChecklistStageSection]):

    @abstractmethod
    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[ChecklistStageSection]:
        """Return all sections for a specific checklist stage."""
        ...
