"""TestMaster — repository port."""

from abc import abstractmethod

from src.domain.entities.masters.test_master import TestMaster
from src.domain.repositories.base_repository import IRepository


class ITestMasterRepository(IRepository[TestMaster]):

    @abstractmethod
    async def exists_by_name(self, test_name: str, exclude_id: int | None = None) -> bool:
        """Check whether a test name is already taken."""
        ...

    @abstractmethod
    async def list_by_product(self, product_id: int) -> list[TestMaster]:
        """Return all tests for a specific product."""
        ...
