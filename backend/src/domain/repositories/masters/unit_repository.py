"""Unit Master — repository port (domain interface)."""

from abc import abstractmethod

from src.domain.entities.masters.unit import Unit
from src.domain.repositories.base_repository import IRepository


class IUnitRepository(IRepository[Unit]):
    """Persistence contract for the Unit master."""

    @abstractmethod
    async def exists_by_name_in_business_unit(
        self, name: str, business_unit_id: int, exclude_id: int | None = None
    ) -> bool:
        """Check if a unit name is already taken within the same business unit."""
        ...

    @abstractmethod
    async def list_by_business_unit(
        self, business_unit_id: int, is_active: bool | None = None
    ) -> list[Unit]:
        """List all units belonging to a specific business unit."""
        ...
