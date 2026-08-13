from abc import abstractmethod
from src.domain.entities.masters.sap_field import SapField
from src.domain.repositories.base_repository import IRepository

class ISapFieldRepository(IRepository[SapField]):
    @abstractmethod
    async def exists_by_field_name(self, field_name: str, exclude_id: int | None = None) -> bool: ...
