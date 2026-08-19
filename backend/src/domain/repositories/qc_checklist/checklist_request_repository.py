"""ChecklistRequest — repository port."""

from abc import abstractmethod

from src.domain.entities.qc_checklist.checklist_request import ChecklistRequest
from src.domain.repositories.base_repository import IRepository


class IChecklistRequestRepository(IRepository[ChecklistRequest]):

    @abstractmethod
    async def exists_by_request_number(self, request_number: str, exclude_id: int | None = None) -> bool:
        """Check whether a request with the given number already exists."""
        ...

    @abstractmethod
    async def get_next_sequence_number(self) -> int:
        """Return the next available sequence number."""
        ...
