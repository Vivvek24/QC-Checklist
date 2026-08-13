"""Stage Master — application service."""

from src.application.dtos.masters.stage_dtos import CreateStageDTO, StageDTO, StageListDTO, UpdateStageDTO
from src.domain.entities.masters.stage import Stage
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.stage_repository import IStageRepository

ENTITY = "Stage"


class StageService:
    def __init__(self, repo: IStageRepository) -> None:
        self._repo = repo

    async def list_stages(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> StageListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        total = await self._repo.count(search=search, is_active=is_active)
        return StageListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def get_stage(self, stage_id: int) -> StageDTO:
        return self._to_dto(await self._require(stage_id))

    async def create_stage(self, dto: CreateStageDTO, actor: User) -> StageDTO:
        if await self._repo.exists_by_name(dto.stage_name):
            raise DuplicateEntityError(ENTITY, "stage_name", dto.stage_name)
        created = await self._repo.create(Stage(stage_name=dto.stage_name.strip(), is_active=dto.is_active, created_by=actor.username, modified_by=actor.username))
        return self._to_dto(created)

    async def update_stage(self, stage_id: int, dto: UpdateStageDTO, actor: User) -> StageDTO:
        stage = await self._require(stage_id)
        if dto.stage_name is not None and dto.stage_name.strip() != stage.stage_name:
            if await self._repo.exists_by_name(dto.stage_name, exclude_id=stage_id):
                raise DuplicateEntityError(ENTITY, "stage_name", dto.stage_name)
            stage.stage_name = dto.stage_name.strip()
        if dto.is_active is not None:
            stage.is_active = dto.is_active
        stage.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(stage))

    async def delete_stage(self, stage_id: int) -> None:
        await self._require(stage_id)
        await self._repo.delete(stage_id)

    async def _require(self, stage_id: int) -> Stage:
        s = await self._repo.get_by_id(stage_id)
        if s is None:
            raise EntityNotFoundError(ENTITY, stage_id)
        return s

    @staticmethod
    def _to_dto(s: Stage) -> StageDTO:
        return StageDTO(id=s.id, stage_name=s.stage_name, is_active=s.is_active,
                        created_by=s.created_by, created_date=s.created_date,
                        modified_by=s.modified_by, modified_date=s.modified_date)
