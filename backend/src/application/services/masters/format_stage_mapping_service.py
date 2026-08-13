"""FormatStageMapping — application service."""

from src.application.dtos.masters.format_stage_mapping_dtos import (
    CreateFormatStageMappingDTO,
    FormatStageMappingDTO,
    FormatStageMappingListDTO,
    UpdateFormatStageMappingDTO,
)
from src.domain.entities.masters.format_stage_mapping import FormatStageMapping
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.format_stage_mapping_repository import IFormatStageMappingRepository

ENTITY = "FormatStageMapping"


class FormatStageMappingService:
    def __init__(self, repo: IFormatStageMappingRepository) -> None:
        self._repo = repo

    async def list_mappings(
        self, skip: int = 0, limit: int = 100, is_active: bool | None = None
    ) -> FormatStageMappingListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, is_active=is_active)
        total = await self._repo.count(is_active=is_active)
        return FormatStageMappingListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def list_by_format(self, format_id: int) -> list[FormatStageMappingDTO]:
        items = await self._repo.list_by_format(format_id)
        return [self._to_dto(i) for i in items]

    async def list_by_stage(self, stage_id: int) -> list[FormatStageMappingDTO]:
        items = await self._repo.list_by_stage(stage_id)
        return [self._to_dto(i) for i in items]

    async def get_mapping(self, mapping_id: int) -> FormatStageMappingDTO:
        return self._to_dto(await self._require(mapping_id))

    async def create_mapping(self, dto: CreateFormatStageMappingDTO, actor: User) -> FormatStageMappingDTO:
        if await self._repo.exists_by_format_and_stage(dto.format_id, dto.stage_id):
            raise DuplicateEntityError(ENTITY, "format_id+stage_id", f"{dto.format_id}+{dto.stage_id}")
        created = await self._repo.create(FormatStageMapping(
            format_id=dto.format_id,
            stage_id=dto.stage_id,
            is_active=dto.is_active,
            is_approvable=dto.is_approvable,
            is_refer_back=dto.is_refer_back,
            has_section=dto.has_section,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_mapping(self, mapping_id: int, dto: UpdateFormatStageMappingDTO, actor: User) -> FormatStageMappingDTO:
        mapping = await self._require(mapping_id)
        format_id = dto.format_id if dto.format_id is not None else mapping.format_id
        stage_id = dto.stage_id if dto.stage_id is not None else mapping.stage_id
        if (format_id != mapping.format_id or stage_id != mapping.stage_id):
            if await self._repo.exists_by_format_and_stage(format_id, stage_id, exclude_id=mapping_id):
                raise DuplicateEntityError(ENTITY, "format_id+stage_id", f"{format_id}+{stage_id}")
        if dto.format_id is not None:
            mapping.format_id = dto.format_id
        if dto.stage_id is not None:
            mapping.stage_id = dto.stage_id
        if dto.is_active is not None:
            mapping.is_active = dto.is_active
        if dto.is_approvable is not None:
            mapping.is_approvable = dto.is_approvable
        if dto.is_refer_back is not None:
            mapping.is_refer_back = dto.is_refer_back
        if dto.has_section is not None:
            mapping.has_section = dto.has_section
        mapping.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(mapping))

    async def delete_mapping(self, mapping_id: int) -> None:
        await self._require(mapping_id)
        await self._repo.delete(mapping_id)

    async def _require(self, mapping_id: int) -> FormatStageMapping:
        m = await self._repo.get_by_id(mapping_id)
        if m is None:
            raise EntityNotFoundError(ENTITY, mapping_id)
        return m

    @staticmethod
    def _to_dto(m: FormatStageMapping) -> FormatStageMappingDTO:
        return FormatStageMappingDTO(
            id=m.id,
            format_id=m.format_id,
            stage_id=m.stage_id,
            is_active=m.is_active,
            is_approvable=m.is_approvable,
            is_refer_back=m.is_refer_back,
            has_section=m.has_section,
            created_by=m.created_by,
            created_date=m.created_date,
            modified_by=m.modified_by,
            modified_date=m.modified_date,
        )
