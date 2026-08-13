"""FormatStageMapping — repository port."""

from abc import abstractmethod

from src.domain.entities.masters.format_stage_mapping import FormatStageMapping
from src.domain.repositories.base_repository import IRepository


class IFormatStageMappingRepository(IRepository[FormatStageMapping]):

    @abstractmethod
    async def exists_by_format_and_stage(self, format_id: int, stage_id: int, exclude_id: int | None = None) -> bool:
        """Check whether a mapping between format and stage already exists."""
        ...

    @abstractmethod
    async def list_by_format(self, format_id: int) -> list[FormatStageMapping]:
        """Return all mappings for a specific format."""
        ...

    @abstractmethod
    async def list_by_stage(self, stage_id: int) -> list[FormatStageMapping]:
        """Return all mappings for a specific stage."""
        ...
