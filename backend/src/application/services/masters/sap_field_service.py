from src.application.dtos.masters.sap_field_dtos import *
from src.domain.entities.masters.sap_field import SapField
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.sap_field_repository import ISapFieldRepository
ENTITY = "SapField"
class SapFieldService:
    def __init__(self, repo: ISapFieldRepository) -> None: self._repo = repo
    async def list_all(self, skip=0, limit=100, search=None, is_active=None) -> SapFieldListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        return SapFieldListDTO(items=[self._d(i) for i in items], total=await self._repo.count(search=search, is_active=is_active), skip=skip, limit=limit)
    async def get(self, id: int) -> SapFieldDTO: return self._d(await self._req(id))
    async def create(self, dto: CreateSapFieldDTO, actor: User) -> SapFieldDTO:
        if await self._repo.exists_by_field_name(dto.field_name): raise DuplicateEntityError(ENTITY, "field_name", dto.field_name)
        return self._d(await self._repo.create(SapField(field_name=dto.field_name.strip(), is_active=dto.is_active, created_by=actor.username, modified_by=actor.username)))
    async def update(self, id: int, dto: UpdateSapFieldDTO, actor: User) -> SapFieldDTO:
        e = await self._req(id)
        if dto.field_name and dto.field_name.strip() != e.field_name:
            if await self._repo.exists_by_field_name(dto.field_name, exclude_id=id): raise DuplicateEntityError(ENTITY, "field_name", dto.field_name)
            e.field_name = dto.field_name.strip()
        if dto.is_active is not None: e.is_active = dto.is_active
        e.mark_modified(actor.username); return self._d(await self._repo.update(e))
    async def delete(self, id: int) -> None: await self._req(id); await self._repo.delete(id)
    async def _req(self, id: int) -> SapField:
        e = await self._repo.get_by_id(id)
        if not e: raise EntityNotFoundError(ENTITY, id)
        return e
    @staticmethod
    def _d(e: SapField) -> SapFieldDTO:
        return SapFieldDTO(id=e.id, field_name=e.field_name, is_active=e.is_active, created_by=e.created_by, created_date=e.created_date, modified_by=e.modified_by, modified_date=e.modified_date)
