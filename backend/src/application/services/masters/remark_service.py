from src.application.dtos.masters.remark_dtos import *
from src.domain.entities.masters.remark import Remark
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.domain.repositories.masters.remark_repository import IRemarkRepository
ENTITY = "Remark"

class RemarkService:
    def __init__(self, repo: IRemarkRepository) -> None: self._repo = repo

    async def list_all(self, skip=0, limit=100, search=None, is_active=None) -> RemarkListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        return RemarkListDTO(items=[self._d(i) for i in items], total=await self._repo.count(search=search, is_active=is_active), skip=skip, limit=limit)

    async def get(self, id: int) -> RemarkDTO: return self._d(await self._req(id))

    async def create(self, dto: CreateRemarkDTO, actor: User) -> RemarkDTO:
        return self._d(await self._repo.create(Remark(
            remark=dto.remark.strip(), role_ids=dto.role_ids, is_active=dto.is_active,
            created_by=actor.username, modified_by=actor.username,
        )))

    async def update(self, id: int, dto: UpdateRemarkDTO, actor: User) -> RemarkDTO:
        e = await self._req(id)
        if dto.remark is not None: e.remark = dto.remark.strip()
        if dto.role_ids is not None: e.role_ids = dto.role_ids
        if dto.is_active is not None: e.is_active = dto.is_active
        e.mark_modified(actor.username)
        return self._d(await self._repo.update(e))

    async def delete(self, id: int) -> None: await self._req(id); await self._repo.delete(id)

    async def _req(self, id: int) -> Remark:
        e = await self._repo.get_by_id(id)
        if not e: raise EntityNotFoundError(ENTITY, id)
        return e

    @staticmethod
    def _d(e: Remark) -> RemarkDTO:
        return RemarkDTO(id=e.id, remark=e.remark, role_ids=e.role_ids, is_active=e.is_active,
                         created_by=e.created_by, created_date=e.created_date,
                         modified_by=e.modified_by, modified_date=e.modified_date)
