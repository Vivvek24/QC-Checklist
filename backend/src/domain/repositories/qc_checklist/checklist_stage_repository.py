"""ChecklistStage — repository port."""

from abc import abstractmethod

from src.domain.entities.qc_checklist.checklist_stage import ChecklistStage
from src.domain.repositories.base_repository import IRepository


class IChecklistStageRepository(IRepository[ChecklistStage]):

    @abstractmethod
    async def list_by_checklist_request(self, checklist_request_id: int) -> list[ChecklistStage]:
        """Return all stages for a specific checklist request."""
        ...
