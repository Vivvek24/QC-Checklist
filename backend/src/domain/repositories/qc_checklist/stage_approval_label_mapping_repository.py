"""StageApprovalLabelMapping — repository port."""

from abc import abstractmethod

from src.domain.entities.qc_checklist.stage_approval_label_mapping import StageApprovalLabelMapping
from src.domain.repositories.base_repository import IRepository


class IStageApprovalLabelMappingRepository(IRepository[StageApprovalLabelMapping]):

    @abstractmethod
    async def list_by_checklist_stage(self, checklist_stage_id: int) -> list[StageApprovalLabelMapping]:
        """Return all approval label mappings for a specific checklist stage."""
        ...

    @abstractmethod
    async def list_by_approval_label(self, approval_label_id: int) -> list[StageApprovalLabelMapping]:
        """Return all mappings for a specific approval label."""
        ...
