"""Format Master — repository port."""

from abc import abstractmethod

from src.domain.entities.masters.format import Format
from src.domain.repositories.base_repository import IRepository


class IFormatRepository(IRepository[Format]):
    """Persistence contract for the Format master."""

    @abstractmethod
    async def exists_by_format_no(self, format_no: str, exclude_id: int | None = None) -> bool:
        """Check whether a format number is already taken."""
        ...
