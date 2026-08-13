"""Format Master — application service."""

from src.application.dtos.masters.format_dtos import (
    CreateFormatDTO,
    FormatDTO,
    FormatListDTO,
    UpdateFormatDTO,
)
from src.domain.entities.masters.format import Format
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.format_repository import IFormatRepository

ENTITY = "Format"


class FormatService:
    def __init__(self, repo: IFormatRepository) -> None:
        self._repo = repo

    async def list_formats(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> FormatListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, search=search, is_active=is_active)
        total = await self._repo.count(search=search, is_active=is_active)
        return FormatListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def get_format(self, format_id: int) -> FormatDTO:
        return self._to_dto(await self._require(format_id))

    async def create_format(self, dto: CreateFormatDTO, actor: User) -> FormatDTO:
        if await self._repo.exists_by_format_no(dto.format_no):
            raise DuplicateEntityError(ENTITY, "format_no", dto.format_no)
        created = await self._repo.create(
            Format(
                format_no=dto.format_no.strip(),
                format_title=dto.format_title.strip(),
                format_name=dto.format_name.strip(),
                unit_id=dto.unit_id,
                format_type=dto.format_type,
                has_declaration_question=dto.has_declaration_question,
                is_active=dto.is_active,
                created_by=actor.username,
                modified_by=actor.username,
            )
        )
        return self._to_dto(created)

    async def update_format(self, format_id: int, dto: UpdateFormatDTO, actor: User) -> FormatDTO:
        fmt = await self._require(format_id)

        if dto.format_no is not None and dto.format_no.strip() != fmt.format_no:
            if await self._repo.exists_by_format_no(dto.format_no, exclude_id=format_id):
                raise DuplicateEntityError(ENTITY, "format_no", dto.format_no)
            fmt.format_no = dto.format_no.strip()

        if dto.format_title is not None:
            fmt.format_title = dto.format_title.strip()
        if dto.format_name is not None:
            fmt.format_name = dto.format_name.strip()
        if dto.unit_id is not None:
            fmt.unit_id = dto.unit_id
        if dto.format_type is not None:
            fmt.format_type = dto.format_type
        if dto.has_declaration_question is not None:
            fmt.has_declaration_question = dto.has_declaration_question
        if dto.is_active is not None:
            fmt.is_active = dto.is_active

        fmt.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(fmt))

    async def delete_format(self, format_id: int) -> None:
        await self._require(format_id)
        await self._repo.delete(format_id)

    async def _require(self, format_id: int) -> Format:
        fmt = await self._repo.get_by_id(format_id)
        if fmt is None:
            raise EntityNotFoundError(ENTITY, format_id)
        return fmt

    @staticmethod
    def _to_dto(fmt: Format) -> FormatDTO:
        return FormatDTO(
            id=fmt.id,
            format_no=fmt.format_no,
            format_title=fmt.format_title,
            format_name=fmt.format_name,
            unit_id=fmt.unit_id,
            format_type=fmt.format_type,
            has_declaration_question=fmt.has_declaration_question,
            is_active=fmt.is_active,
            created_by=fmt.created_by,
            created_date=fmt.created_date,
            modified_by=fmt.modified_by,
            modified_date=fmt.modified_date,
        )
