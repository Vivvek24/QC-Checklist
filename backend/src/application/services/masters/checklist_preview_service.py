"""Checklist Preview — application service.

Builds a full checklist preview from master data without persisting
anything: the format -> stages -> sections -> questions tree, plus each
stage/section's Template Studio column layout. Read-only, shared by
Template Studio (the config editor) and Create Request (the fill-in form)
so both render from one call instead of separate per-stage lookups.

Depends only on repository ports — never touches SQLAlchemy or an
AsyncSession directly; every read goes through a repository interface.
"""

from src.application.dtos.masters.checklist_preview_dtos import (
    ApprovalLabelPreviewDTO,
    ChecklistPreviewDTO,
    ChecklistStagePreviewDTO,
    ColumnPreviewDTO,
    QuestionAnswerPreviewDTO,
    QuestionOptionPreviewDTO,
    SectionPreviewDTO,
)
from src.domain.entities.masters.question import Question
from src.domain.entities.masters.question_option import QuestionOption
from src.domain.entities.masters.stage_question_mapping import StageQuestionMapping
from src.domain.entities.masters.template import TemplateLayoutColumn
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.domain.repositories.masters.approval_label_repository import IApprovalLabelRepository
from src.domain.repositories.masters.format_repository import IFormatRepository
from src.domain.repositories.masters.format_stage_mapping_repository import (
    IFormatStageMappingRepository,
)
from src.domain.repositories.masters.question_option_repository import IQuestionOptionRepository
from src.domain.repositories.masters.question_repository import IQuestionRepository
from src.domain.repositories.masters.question_sub_question_repository import (
    IQuestionSubQuestionRepository,
)
from src.domain.repositories.masters.section_repository import ISectionRepository
from src.domain.repositories.masters.stage_question_mapping_repository import (
    IStageQuestionMappingRepository,
)
from src.domain.repositories.masters.stage_repository import IStageRepository
from src.domain.repositories.masters.template_layout_column_repository import (
    ITemplateLayoutColumnRepository,
)
from src.domain.repositories.masters.unit_repository import IUnitRepository


class _QuestionMetadata:
    """Pre-fetched question metadata, keyed by question_id, for one batch of
    questions (and their options/response-options). Internal helper — not a
    DTO, just avoids passing seven separate dicts positionally."""

    def __init__(self, questions: list[Question], options: list[QuestionOption]) -> None:
        self.by_id: dict[int, Question] = {q.id: q for q in questions}
        self.options: dict[int, list[QuestionOptionPreviewDTO]] = {}
        self.response_options: dict[int, list[QuestionOptionPreviewDTO]] = {}
        for opt in options:
            bucket = self.response_options if opt.is_response_option else self.options
            bucket.setdefault(opt.question_id, []).append(
                QuestionOptionPreviewDTO(id=opt.id, label=opt.option_title)
            )

    def title(self, qid: int) -> str:
        q = self.by_id.get(qid)
        return q.title if q else ""

    def answer_type(self, qid: int) -> str:
        q = self.by_id.get(qid)
        return q.answer_type.value if q else ""

    def has_text_box(self, qid: int) -> bool:
        q = self.by_id.get(qid)
        return q.has_text_box if q else False

    def has_multiple_text_box(self, qid: int) -> bool:
        q = self.by_id.get(qid)
        return q.has_multiple_text_box if q else False

    def has_sub_question(self, qid: int) -> bool:
        q = self.by_id.get(qid)
        return q.has_sub_question if q else False


def _to_column_preview(c: TemplateLayoutColumn) -> ColumnPreviewDTO:
    return ColumnPreviewDTO(
        id=c.id,
        header=c.header,
        column_type=c.column_type.value,
        display_order=c.display_order,
        width=c.width,
        is_required=c.is_required,
    )


class ChecklistPreviewService:
    """Builds a full checklist preview from master data without persisting anything."""

    def __init__(
        self,
        format_repo: IFormatRepository,
        unit_repo: IUnitRepository,
        format_stage_mapping_repo: IFormatStageMappingRepository,
        stage_repo: IStageRepository,
        stage_question_mapping_repo: IStageQuestionMappingRepository,
        question_repo: IQuestionRepository,
        question_option_repo: IQuestionOptionRepository,
        question_sub_question_repo: IQuestionSubQuestionRepository,
        section_repo: ISectionRepository,
        approval_label_repo: IApprovalLabelRepository,
        column_repo: ITemplateLayoutColumnRepository,
    ) -> None:
        self._format_repo = format_repo
        self._unit_repo = unit_repo
        self._format_stage_mapping_repo = format_stage_mapping_repo
        self._stage_repo = stage_repo
        self._stage_question_mapping_repo = stage_question_mapping_repo
        self._question_repo = question_repo
        self._question_option_repo = question_option_repo
        self._question_sub_question_repo = question_sub_question_repo
        self._section_repo = section_repo
        self._approval_label_repo = approval_label_repo
        self._column_repo = column_repo

    async def _fetch_question_metadata(self, question_ids: list[int]) -> _QuestionMetadata:
        """Bulk-load questions and their options for one batch of question ids."""
        if not question_ids:
            return _QuestionMetadata([], [])
        questions = await self._question_repo.list_by_ids(question_ids)
        options = await self._question_option_repo.list_by_questions(question_ids)
        return _QuestionMetadata(questions, options)

    async def _build_sub_questions_map(
        self, question_ids: list[int], meta: _QuestionMetadata
    ) -> dict[int, list[QuestionAnswerPreviewDTO]]:
        """Given questions that may have sub-questions, load and preview them."""
        parent_ids = [qid for qid in question_ids if meta.has_sub_question(qid)]
        if not parent_ids:
            return {}
        sub_ids_by_parent = await self._question_sub_question_repo.list_sub_question_ids_by_parents(
            parent_ids
        )
        all_sub_ids = list({sid for ids in sub_ids_by_parent.values() for sid in ids})
        if not all_sub_ids:
            return {}
        sub_meta = await self._fetch_question_metadata(all_sub_ids)

        sub_questions_map: dict[int, list[QuestionAnswerPreviewDTO]] = {}
        for parent_id, sub_ids in sub_ids_by_parent.items():
            sub_questions_map[parent_id] = [
                QuestionAnswerPreviewDTO(
                    stage_question_mapping_id=0,
                    question_id=sid,
                    question_title=sub_meta.title(sid),
                    serial_number=0,
                    section_id=None,
                    section_name=None,
                    show_on_grid=False,
                    answer_type=sub_meta.answer_type(sid),
                    has_text_box=sub_meta.has_text_box(sid),
                    has_multiple_text_box=sub_meta.has_multiple_text_box(sid),
                    has_sub_question=False,
                    is_declaration_question=False,
                    aql_limit="",
                    sap_field_id=None,
                    is_editable=True,
                    custom_answers=None,
                    sub_questions=[],
                    options=sub_meta.options.get(sid, []),
                    response_options=sub_meta.response_options.get(sid, []),
                )
                for sid in sub_ids
            ]
        return sub_questions_map

    @staticmethod
    def _to_question_answer_preview(
        sqm: StageQuestionMapping,
        meta: _QuestionMetadata,
        sub_questions_map: dict[int, list[QuestionAnswerPreviewDTO]],
        section_name: str | None,
    ) -> QuestionAnswerPreviewDTO:
        qid = sqm.question_id
        return QuestionAnswerPreviewDTO(
            stage_question_mapping_id=sqm.id,
            question_id=qid,
            question_title=meta.title(qid),
            serial_number=sqm.serial_number,
            section_id=sqm.section_id,
            section_name=section_name,
            show_on_grid=sqm.show_on_grid,
            answer_type=meta.answer_type(qid),
            has_text_box=meta.has_text_box(qid),
            has_multiple_text_box=meta.has_multiple_text_box(qid),
            has_sub_question=meta.has_sub_question(qid),
            is_declaration_question=sqm.is_declaration_question,
            aql_limit=sqm.aql_limit,
            sap_field_id=sqm.sap_field_id,
            is_editable=sqm.is_editable,
            custom_answers=sqm.custom_answers.value if sqm.custom_answers else None,
            sub_questions=sub_questions_map.get(qid, []),
            options=meta.options.get(qid, []),
            response_options=meta.response_options.get(qid, []),
        )

    async def build_questions_for_stage(
        self, fsm_id: int, has_section: bool
    ) -> tuple[list[QuestionAnswerPreviewDTO], list[SectionPreviewDTO], list[ColumnPreviewDTO]]:
        """
        Given a format_stage_mapping_id, builds:
        - questions list (non-sectioned questions)
        - sections list (each section with its own questions and columns)
        - columns list (this stage's own Template Studio column layout)
        """
        sqm_list = await self._stage_question_mapping_repo.list_by_format_stage_mapping(fsm_id)

        q_ids = [sqm.question_id for sqm in sqm_list if sqm.question_id]
        meta = await self._fetch_question_metadata(q_ids)
        sub_questions_map = await self._build_sub_questions_map(q_ids, meta)

        all_columns = await self._column_repo.list_for_stage(fsm_id)
        stage_columns = [_to_column_preview(c) for c in all_columns if c.section_id is None]
        columns_by_section: dict[int, list[ColumnPreviewDTO]] = {}
        for c in all_columns:
            if c.section_id is not None:
                columns_by_section.setdefault(c.section_id, []).append(_to_column_preview(c))

        section_map: dict[int, str] = {}
        sections_preview: list[SectionPreviewDTO] = []

        if has_section:
            all_sections = await self._section_repo.list_by_format_stage_mapping(fsm_id)
            for sec in all_sections:
                section_map[sec.id] = sec.section_name

            for sec in all_sections:
                sec_questions = [
                    self._to_question_answer_preview(sqm, meta, sub_questions_map, sec.section_name)
                    for sqm in sqm_list
                    if sqm.section_id == sec.id
                ]
                sections_preview.append(SectionPreviewDTO(
                    section_id=sec.id,
                    section_name=sec.section_name,
                    questions=sec_questions,
                    columns=columns_by_section.get(sec.id, []),
                ))

        questions: list[QuestionAnswerPreviewDTO] = []
        for sqm in sqm_list:
            if has_section and sqm.section_id:
                continue
            questions.append(self._to_question_answer_preview(
                sqm, meta, sub_questions_map,
                section_map.get(sqm.section_id) if sqm.section_id else None,
            ))

        return questions, sections_preview, stage_columns

    async def get_preview(self, format_id: int) -> ChecklistPreviewDTO:
        """
        Returns the complete checklist structure for a given format.
        Nothing is persisted.
        """
        fmt = await self._format_repo.get_by_id(format_id)
        if fmt is None:
            raise EntityNotFoundError("Format", format_id)

        unit_name = ""
        if fmt.unit_id:
            unit = await self._unit_repo.get_by_id(fmt.unit_id)
            if unit:
                unit_name = unit.name

        format_stage_mappings = await self._format_stage_mapping_repo.list_by_format(format_id)

        stage_ids = [fsm.stage_id for fsm in format_stage_mappings]
        stages = await self._stage_repo.list_by_ids(stage_ids)
        stage_map: dict[int, str] = {s.id: s.stage_name for s in stages}

        checklist_stages: list[ChecklistStagePreviewDTO] = []

        for idx, fsm in enumerate(format_stage_mappings):
            questions, sections_preview, stage_columns = await self.build_questions_for_stage(
                fsm.id, fsm.has_section
            )

            approval_labels = [
                ApprovalLabelPreviewDTO(approval_label_id=al.id, label=al.label)
                for al in await self._approval_label_repo.list_active_by_stage(fsm.stage_id)
            ]

            checklist_stages.append(ChecklistStagePreviewDTO(
                format_stage_mapping_id=fsm.id,
                stage_id=fsm.stage_id,
                stage_name=stage_map.get(fsm.stage_id, f"Stage {fsm.stage_id}"),
                is_approvable=fsm.is_approvable,
                has_section=fsm.has_section,
                status="Initial" if idx < 2 else "",
                questions=questions,
                sections=sections_preview,
                approval_labels=approval_labels,
                columns=stage_columns,
            ))

        return ChecklistPreviewDTO(
            format_id=fmt.id,
            format_name=fmt.format_name,
            format_no=fmt.format_no,
            format_type=fmt.format_type.value,
            has_declaration_question=fmt.has_declaration_question,
            unit_name=unit_name,
            stages=checklist_stages,
        )
