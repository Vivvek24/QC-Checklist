"""Section Master — repository port."""

from abc import abstractmethod

from src.domain.entities.masters.section import Section
from src.domain.repositories.base_repository import IRepository


class ISectionRepository(IRepository[Section]):

    @abstractmethod
    async def exists_by_name(self, section_name: str, exclude_id: int | None = None) -> bool:
        """Check whether a section name is already taken."""
        ...

    @abstractmethod
    async def list_by_format_stage_mapping(self, format_stage_mapping_id: int) -> list[Section]:
        """Return all sections under one stage mapping, in id order."""
        ...
