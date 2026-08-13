from abc import abstractmethod
from src.domain.entities.masters.validation_type import ValidationType
from src.domain.repositories.base_repository import IRepository

class IValidationTypeRepository(IRepository[ValidationType]):
    @abstractmethod
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool: ...
