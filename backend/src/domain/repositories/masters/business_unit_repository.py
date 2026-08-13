"""
Business Unit Master — repository port (domain interface).
"""

from abc import abstractmethod

from src.domain.entities.masters.business_unit import BusinessUnit
from src.domain.repositories.base_repository import IRepository


class IBusinessUnitRepository(IRepository[BusinessUnit]):
    """Persistence contract for the Business Unit master."""

    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool:
        """Check whether a business unit name is already taken, optionally ignoring one row."""
        ...
