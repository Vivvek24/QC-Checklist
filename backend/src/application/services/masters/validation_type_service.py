from src.application.dtos.masters.validation_type_dtos import *
from src.domain.entities.masters.validation_type import ValidationType
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.validation_type_repository import IValidationTypeRepository
ENTITY = "ValidationType"
class ValidationTypeService:
    def __init__(self, repo: IValidationTypeRepository) -> None: self._repo = repo
    async def list_all(self, skip=0, limit=100, search=None, is_active=None) -> ValidationTypeListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        return ValidationTypeListDTO(items=[self._d(i) for i in items], total=await self._repo.count(search=search, is_active=is_active), skip=skip, limit=limit)
    async def get(self, id: int) -> ValidationTypeDTO: return self._d(await self._req(id))
    async def create(self, dto: CreateValidationTypeDTO, actor: User) -> ValidationTypeDTO:
        if await self._repo.exists_by_name(dto.name): raise DuplicateEntityError(ENTITY, "name", dto.name)
        return self._d(await self._repo.create(ValidationType(name=dto.name.strip(), is_active=dto.is_active, created_by=actor.username, modified_by=actor.username)))
    async def update(self, id: int, dto: UpdateValidationTypeDTO, actor: User) -> ValidationTypeDTO:
        e = await self._req(id)
        if dto.name and dto.name.strip() != e.name:
            if await self._repo.exists_by_name(dto.name, exclude_id=id): raise DuplicateEntityError(ENTITY, "name", dto.name)
            e.name = dto.name.strip()
        if dto.is_active is not None: e.is_active = dto.is_active
        e.mark_modified(actor.username); return self._d(await self._repo.update(e))
    async def delete(self, id: int) -> None: await self._req(id); await self._repo.delete(id)
    async def _req(self, id: int) -> ValidationType:
        e = await self._repo.get_by_id(id)
        if not e: raise EntityNotFoundError(ENTITY, id)
        return e
    @staticmethod
    def _d(e: ValidationType) -> ValidationTypeDTO:
        return ValidationTypeDTO(id=e.id, name=e.name, is_active=e.is_active, created_by=e.created_by, created_date=e.created_date, modified_by=e.modified_by, modified_date=e.modified_date)
