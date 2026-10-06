"""Stage Master — repository port."""

from abc import abstractmethod

from src.domain.entities.masters.stage import Stage
from src.domain.repositories.base_repository import IRepository


class IStageRepository(IRepository[Stage]):

    @abstractmethod
    async def exists_by_name(self, stage_name: str, exclude_id: int | None = None) -> bool:
        """Check whether a stage name is already taken."""
        ...

    @abstractmethod
    async def list_by_ids(self, stage_ids: list[int]) -> list[Stage]:
        """Bulk-load stages by id. Returns only the ones that exist."""
        ...
