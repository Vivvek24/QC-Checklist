from abc import abstractmethod
from src.domain.entities.masters.remark import Remark
from src.domain.repositories.base_repository import IRepository


class IRemarkRepository(IRepository[Remark]):

    @abstractmethod
    async def exists_by_remark(self, remark: str, exclude_id: int | None = None) -> bool: ...
