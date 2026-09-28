"""Template Stage Save — application service.

Atomically saves everything Template Studio owns for a single stage: its own
rows (stage_question_mappings) + columns (template_layout_columns), and each
nested section's rows + columns, plus any rows/sections the user removed from
the canvas since the last save.

All of this runs against one request-scoped AsyncSession shared by every
repository constructed here (see the controller's _get_service). The session
never commits itself — src.infrastructure.database.session.get_db_session
commits once, after the endpoint returns, or rolls back everything if this
service raises. That's what makes the whole stage save all-or-nothing.
"""

from src.application.dtos.masters.template_dtos import ColumnInputDTO, ReplaceColumnsForScopeDTO
from src.application.dtos.masters.template_stage_save_dtos import (
    StageSaveColumnDTO,
    StageSaveRowDTO,
    StageSaveRowResultDTO,
    StageSaveSectionDTO,
    StageSaveSectionResultDTO,
    TemplateStageSaveDTO,
    TemplateStageSaveResultDTO,
)
from src.application.services.masters.format_stage_mapping_service import FormatStageMappingService
from src.application.services.masters.template_service import TemplateService
from src.domain.entities.masters.section import Section
from src.domain.entities.masters.stage_question_mapping import StageQuestionMapping
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import BusinessRuleViolationError, DuplicateEntityError
from src.domain.repositories.masters.section_repository import ISectionRepository
from src.domain.repositories.masters.stage_question_mapping_repository import (
    IStageQuestionMappingRepository,
)

ENTITY = "StageQuestionMapping"


class TemplateStageSaveService:
    def __init__(
        self,
        mapping_repo: IStageQuestionMappingRepository,
        section_repo: ISectionRepository,
        template_service: TemplateService,
        format_stage_mapping_service: FormatStageMappingService,
    ) -> None:
        self._mapping_repo = mapping_repo
        self._section_repo = section_repo
        self._template_service = template_service
        self._format_stage_mapping_service = format_stage_mapping_service

    async def save_stage(
        self, dto: TemplateStageSaveDTO, actor: User
    ) -> TemplateStageSaveResultDTO:
        self._validate(dto)

        # The stage picker lists every stage from the Stage master, so a
        # freshly-picked stage may not have a format_stage_mapping row yet.
        # Resolve (or create) it before doing anything else — everything
        # below hangs off this id.
        fsm = await self._format_stage_mapping_service.get_or_create_for_format_and_stage(
            dto.format_id, dto.stage_id, actor
        )
        format_stage_mapping_id = fsm.id

        # Deletions first — a section's rows must go before the section
        # itself (mappings don't cascade on section delete).
        for mapping_id in dto.deleted_mapping_ids:
            await self._mapping_repo.delete(mapping_id)
        for section_id in dto.deleted_section_ids:
            await self._section_repo.delete(section_id)

        # Stage-level rows + columns.
        saved_rows = await self._save_rows(dto.rows, format_stage_mapping_id, None, actor)
        await self._template_service.replace_columns_for_scope(
            ReplaceColumnsForScopeDTO(
                format_id=dto.format_id,
                format_stage_mapping_id=format_stage_mapping_id,
                section_id=None,
                columns=[self._to_column_input(c) for c in dto.columns],
            ),
            actor,
        )

        # Each section: create/rename, then its own rows + columns.
        saved_sections: list[StageSaveSectionResultDTO] = []
        for section in dto.sections:
            section_id = await self._save_section(section, format_stage_mapping_id, actor)
            section_rows = await self._save_rows(
                section.rows, format_stage_mapping_id, section_id, actor
            )
            await self._template_service.replace_columns_for_scope(
                ReplaceColumnsForScopeDTO(
                    format_id=dto.format_id,
                    format_stage_mapping_id=format_stage_mapping_id,
                    section_id=section_id,
                    columns=[self._to_column_input(c) for c in section.columns],
                ),
                actor,
            )
            saved_sections.append(
                StageSaveSectionResultDTO(
                    id=section_id, section_name=section.section_name, rows=section_rows
                )
            )

        return TemplateStageSaveResultDTO(
            format_stage_mapping_id=format_stage_mapping_id,
            rows=saved_rows,
            sections=saved_sections,
        )

    async def _save_rows(
        self,
        rows: list[StageSaveRowDTO],
        format_stage_mapping_id: int,
        section_id: int | None,
        actor: User,
    ) -> list[StageSaveRowResultDTO]:
        results: list[StageSaveRowResultDTO] = []
        for index, row in enumerate(rows):
            serial_number = index + 1
            if row.mapping_id:
                if await self._mapping_repo.exists_by_mapping_and_question(
                    format_stage_mapping_id, row.question_id, exclude_id=row.mapping_id
                ):
                    raise DuplicateEntityError(
                        ENTITY, "format_stage_mapping_id+question_id",
                        f"{format_stage_mapping_id}+{row.question_id}",
                    )
                saved = await self._mapping_repo.update(
                    StageQuestionMapping(
                        id=row.mapping_id,
                        format_stage_mapping_id=format_stage_mapping_id,
                        question_id=row.question_id,
                        sap_field_id=row.sap_field_id,
                        section_id=section_id,
                        serial_number=serial_number,
                        show_on_grid=row.show_on_grid,
                        aql_limit=row.aql_limit,
                        is_declaration_question=row.is_declaration_question,
                        is_editable=row.is_editable,
                        custom_answers=row.custom_answers,
                        is_active=row.is_active,
                        modified_by=actor.username,
                    )
                )
            else:
                if await self._mapping_repo.exists_by_mapping_and_question(
                    format_stage_mapping_id, row.question_id
                ):
                    raise DuplicateEntityError(
                        ENTITY, "format_stage_mapping_id+question_id",
                        f"{format_stage_mapping_id}+{row.question_id}",
                    )
                saved = await self._mapping_repo.create(
                    StageQuestionMapping(
                        format_stage_mapping_id=format_stage_mapping_id,
                        question_id=row.question_id,
                        sap_field_id=row.sap_field_id,
                        section_id=section_id,
                        serial_number=serial_number,
                        show_on_grid=row.show_on_grid,
                        aql_limit=row.aql_limit,
                        is_declaration_question=row.is_declaration_question,
                        is_editable=row.is_editable,
                        custom_answers=row.custom_answers,
                        is_active=row.is_active,
                        created_by=actor.username,
                        modified_by=actor.username,
                    )
                )
            results.append(
                StageSaveRowResultDTO(
                    id=saved.id, question_id=saved.question_id, serial_number=saved.serial_number
                )
            )
        return results

    async def _save_section(
        self, section: StageSaveSectionDTO, format_stage_mapping_id: int, actor: User
    ) -> int:
        name = section.section_name.strip() or "Untitled Section"
        if section.section_id:
            saved = await self._section_repo.update(
                Section(
                    id=section.section_id,
                    section_name=name,
                    format_stage_mapping_id=format_stage_mapping_id,
                    is_active=True,
                    modified_by=actor.username,
                )
            )
        else:
            saved = await self._section_repo.create(
                Section(
                    section_name=name,
                    format_stage_mapping_id=format_stage_mapping_id,
                    is_active=True,
                    created_by=actor.username,
                    modified_by=actor.username,
                )
            )
        return saved.id

    @staticmethod
    def _to_column_input(c: StageSaveColumnDTO) -> ColumnInputDTO:
        return ColumnInputDTO(
            header=c.header, column_type=c.column_type, display_order=0,
            width=c.width, is_required=c.is_required,
        )

    @staticmethod
    def _validate(dto: TemplateStageSaveDTO) -> None:
        if dto.format_id <= 0:
            raise BusinessRuleViolationError("A valid format_id is required")
        if dto.stage_id <= 0:
            raise BusinessRuleViolationError("A valid stage_id is required")

        def check_rows(rows: list[StageSaveRowDTO], label: str) -> None:
            counts: dict[int, int] = {}
            for row in rows:
                if not row.question_id:
                    raise BusinessRuleViolationError(
                        f"{label} has a row with no question selected."
                    )
                counts[row.question_id] = counts.get(row.question_id, 0) + 1
            dupes = [qid for qid, n in counts.items() if n > 1]
            if dupes:
                raise BusinessRuleViolationError(
                    f"{label} has the same question selected on more than one row."
                )

        check_rows(dto.rows, "This stage")
        for section in dto.sections:
            check_rows(section.rows, f"Section '{section.section_name or 'Untitled Section'}'")
