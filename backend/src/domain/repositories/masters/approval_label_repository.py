from abc import abstractmethod
from src.domain.entities.masters.approval_label import ApprovalLabel
from src.domain.repositories.base_repository import IRepository

class IApprovalLabelRepository(IRepository[ApprovalLabel]):
    @abstractmethod
    async def exists_by_label(self, label: str, exclude_id: int | None = None) -> bool: ...

    @abstractmethod
    async def exists_by_label_for_stage(self, label: str, stage_id: int, exclude_id: int | None = None) -> bool:
        """Check whether a label already exists for a given stage."""
        ...

    @abstractmethod
    async def list_active_by_stage(self, stage_id: int) -> list[ApprovalLabel]:
        """Return all active approval labels for a given stage, in id order."""
        ...
