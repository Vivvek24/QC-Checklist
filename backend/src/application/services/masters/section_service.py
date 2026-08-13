"""Section Master — application service."""

from src.application.dtos.masters.section_dtos import CreateSectionDTO, SectionDTO, SectionListDTO, UpdateSectionDTO
from src.domain.entities.masters.section import Section
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.section_repository import ISectionRepository

ENTITY = "Section"


class SectionService:
    def __init__(self, repo: ISectionRepository) -> None:
        self._repo = repo

    async def list_sections(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None, format_stage_mapping_id: int | None = None) -> SectionListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active, format_stage_mapping_id=format_stage_mapping_id)
        total = await self._repo.count(search=search, is_active=is_active, format_stage_mapping_id=format_stage_mapping_id)
        return SectionListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def get_section(self, section_id: int) -> SectionDTO:
        return self._to_dto(await self._require(section_id))

    async def create_section(self, dto: CreateSectionDTO, actor: User) -> SectionDTO:
        if await self._repo.exists_by_name(dto.section_name):
            raise DuplicateEntityError(ENTITY, "section_name", dto.section_name)
        created = await self._repo.create(Section(
            section_name=dto.section_name.strip(),
            format_stage_mapping_id=dto.format_stage_mapping_id,
            is_active=dto.is_active,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_section(self, section_id: int, dto: UpdateSectionDTO, actor: User) -> SectionDTO:
        section = await self._require(section_id)
        if dto.section_name is not None and dto.section_name.strip() != section.section_name:
            if await self._repo.exists_by_name(dto.section_name, exclude_id=section_id):
                raise DuplicateEntityError(ENTITY, "section_name", dto.section_name)
            section.section_name = dto.section_name.strip()
        if dto.format_stage_mapping_id is not None:
            section.format_stage_mapping_id = dto.format_stage_mapping_id
        if dto.is_active is not None:
            section.is_active = dto.is_active
        section.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(section))

    async def delete_section(self, section_id: int) -> None:
        await self._require(section_id)
        await self._repo.delete(section_id)

    async def _require(self, section_id: int) -> Section:
        s = await self._repo.get_by_id(section_id)
        if s is None:
            raise EntityNotFoundError(ENTITY, section_id)
        return s

    @staticmethod
    def _to_dto(s: Section) -> SectionDTO:
        return SectionDTO(
            id=s.id,
            section_name=s.section_name,
            format_stage_mapping_id=s.format_stage_mapping_id,
            is_active=s.is_active,
            created_by=s.created_by,
            created_date=s.created_date,
            modified_by=s.modified_by,
            modified_date=s.modified_date,
        )
