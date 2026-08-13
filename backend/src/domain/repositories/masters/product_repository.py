"""Product Master — repository port."""

from abc import abstractmethod
from src.domain.entities.masters.product import Product
from src.domain.repositories.base_repository import IRepository


class IProductRepository(IRepository[Product]):

    @abstractmethod
    async def exists_by_name(self, product_name: str, exclude_id: int | None = None) -> bool: ...
