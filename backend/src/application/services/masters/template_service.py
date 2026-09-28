"""Template — application service.

Holds the business rules for a format's template and its checklist column
layout. Depends only on repository ports; returns DTOs; raises domain errors
(never HTTP).
"""

from src.application.dtos.masters.template_dtos import (
    ColumnInputDTO,
    ReplaceColumnsForScopeDTO,
    TemplateDTO,
    TemplateLayoutColumnDTO,
)
from src.domain.entities.masters.template import Template, TemplateLayoutColumn
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import BusinessRuleViolationError
from src.domain.repositories.masters.template_layout_column_repository import (
    ITemplateLayoutColumnRepository,
)
from src.domain.repositories.masters.template_repository import ITemplateRepository


class TemplateService:
    def __init__(
        self,
        template_repo: ITemplateRepository,
        column_repo: ITemplateLayoutColumnRepository,
    ) -> None:
        self._template_repo = template_repo
        self._column_repo = column_repo

    async def get_or_create_for_format(self, format_id: int, actor: User) -> TemplateDTO:
        """Return the format's template, creating it if it doesn't exist yet."""
        existing = await self._template_repo.get_by_format_id(format_id)
        if existing is not None:
            return self._template_to_dto(existing)
        created = await self._template_repo.create(
            Template(format_id=format_id, created_by=actor.username, modified_by=actor.username)
        )
        return self._template_to_dto(created)

    async def list_columns_for_scope(
        self, format_stage_mapping_id: int, section_id: int | None
    ) -> list[TemplateLayoutColumnDTO]:
        columns = await self._column_repo.list_for_scope(format_stage_mapping_id, section_id)
        return [self._column_to_dto(c) for c in columns]

    async def list_columns_for_stage(
        self, format_stage_mapping_id: int
    ) -> list[TemplateLayoutColumnDTO]:
        columns = await self._column_repo.list_for_stage(format_stage_mapping_id)
        return [self._column_to_dto(c) for c in columns]

    async def replace_columns_for_scope(
        self, dto: ReplaceColumnsForScopeDTO, actor: User
    ) -> list[TemplateLayoutColumnDTO]:
        self._validate(dto)
        template = await self._template_repo.get_by_format_id(dto.format_id)
        if template is None:
            template = await self._template_repo.create(
                Template(
                    format_id=dto.format_id,
                    created_by=actor.username,
                    modified_by=actor.username,
                )
            )

        columns = [
            TemplateLayoutColumn(
                header=c.header.strip(),
                column_type=c.column_type,
                display_order=index,
                width=(c.width.strip() if c.width and c.width.strip() else None),
                is_required=c.is_required,
                created_by=actor.username,
                modified_by=actor.username,
            )
            for index, c in enumerate(dto.columns)
        ]
        saved = await self._column_repo.replace_for_scope(
            template.id, dto.format_stage_mapping_id, dto.section_id, columns
        )
        return [self._column_to_dto(c) for c in saved]

    async def delete_columns_for_scope(
        self, format_stage_mapping_id: int, section_id: int | None
    ) -> None:
        await self._column_repo.delete_for_scope(format_stage_mapping_id, section_id)

    @staticmethod
    def _validate(dto: ReplaceColumnsForScopeDTO) -> None:
        if dto.format_id <= 0:
            raise BusinessRuleViolationError("A valid format_id is required")
        if dto.format_stage_mapping_id <= 0:
            raise BusinessRuleViolationError("A valid stage (format_stage_mapping_id) is required")

    @staticmethod
    def _template_to_dto(t: Template) -> TemplateDTO:
        return TemplateDTO(
            id=t.id,
            format_id=t.format_id,
            is_active=t.is_active,
            created_by=t.created_by,
            created_date=t.created_date,
            modified_by=t.modified_by,
            modified_date=t.modified_date,
        )

    @staticmethod
    def _column_to_dto(c: TemplateLayoutColumn) -> TemplateLayoutColumnDTO:
        return TemplateLayoutColumnDTO(
            id=c.id,
            template_id=c.template_id,
            format_stage_mapping_id=c.format_stage_mapping_id,
            section_id=c.section_id,
            header=c.header,
            column_type=c.column_type,
            display_order=c.display_order,
            width=c.width,
            is_required=c.is_required,
        )


__all__ = ["TemplateService", "ColumnInputDTO"]
