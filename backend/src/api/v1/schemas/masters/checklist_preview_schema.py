"""Checklist Preview — Pydantic response schemas.

Each schema owns its own from_dto translation from the application layer's
DTOs so the controller stays a pure HTTP layer: parse the request, call the
service, translate the result — no DTO field-by-field mapping there.
"""

from __future__ import annotations

from pydantic import BaseModel

from src.application.dtos.masters.checklist_preview_dtos import (
    ApprovalLabelPreviewDTO,
    ChecklistPreviewDTO,
    ChecklistStagePreviewDTO,
    ColumnPreviewDTO,
    QuestionAnswerPreviewDTO,
    QuestionOptionPreviewDTO,
    SectionPreviewDTO,
)


class QuestionOptionSchema(BaseModel):
    id: int
    label: str

    @classmethod
    def from_dto(cls, dto: QuestionOptionPreviewDTO) -> QuestionOptionSchema:
        return cls(id=dto.id, label=dto.label)


class QuestionAnswerPreview(BaseModel):
    stage_question_mapping_id: int
    question_id: int
    question_title: str
    serial_number: int
    section_id: int | None = None
    section_name: str | None = None
    show_on_grid: bool = False
    answer_type: str = ""
    has_text_box: bool = False
    has_multiple_text_box: bool = False
    has_sub_question: bool = False
    is_declaration_question: bool = False
    aql_limit: str = ""
    sap_field_id: int | None = None
    is_editable: bool = True
    custom_answers: str | None = None
    sub_questions: list[QuestionAnswerPreview] = []
    options: list[QuestionOptionSchema] = []
    response_options: list[QuestionOptionSchema] = []

    @classmethod
    def from_dto(cls, dto: QuestionAnswerPreviewDTO) -> QuestionAnswerPreview:
        return cls(
            stage_question_mapping_id=dto.stage_question_mapping_id,
            question_id=dto.question_id,
            question_title=dto.question_title,
            serial_number=dto.serial_number,
            section_id=dto.section_id,
            section_name=dto.section_name,
            show_on_grid=dto.show_on_grid,
            answer_type=dto.answer_type,
            has_text_box=dto.has_text_box,
            has_multiple_text_box=dto.has_multiple_text_box,
            has_sub_question=dto.has_sub_question,
            is_declaration_question=dto.is_declaration_question,
            aql_limit=dto.aql_limit,
            sap_field_id=dto.sap_field_id,
            is_editable=dto.is_editable,
            custom_answers=dto.custom_answers,
            sub_questions=[cls.from_dto(sq) for sq in dto.sub_questions],
            options=[QuestionOptionSchema.from_dto(o) for o in dto.options],
            response_options=[QuestionOptionSchema.from_dto(o) for o in dto.response_options],
        )


class ApprovalLabelPreview(BaseModel):
    approval_label_id: int
    label: str

    @classmethod
    def from_dto(cls, dto: ApprovalLabelPreviewDTO) -> ApprovalLabelPreview:
        return cls(approval_label_id=dto.approval_label_id, label=dto.label)


class ColumnPreview(BaseModel):
    id: int
    header: str
    column_type: str
    display_order: int
    width: str | None = None
    is_required: bool = False

    @classmethod
    def from_dto(cls, dto: ColumnPreviewDTO) -> ColumnPreview:
        return cls(
            id=dto.id,
            header=dto.header,
            column_type=dto.column_type,
            display_order=dto.display_order,
            width=dto.width,
            is_required=dto.is_required,
        )


class SectionPreview(BaseModel):
    section_id: int
    section_name: str
    questions: list[QuestionAnswerPreview]
    columns: list[ColumnPreview] = []

    @classmethod
    def from_dto(cls, dto: SectionPreviewDTO) -> SectionPreview:
        return cls(
            section_id=dto.section_id,
            section_name=dto.section_name,
            questions=[QuestionAnswerPreview.from_dto(q) for q in dto.questions],
            columns=[ColumnPreview.from_dto(c) for c in dto.columns],
        )


class ChecklistStagePreview(BaseModel):
    format_stage_mapping_id: int
    stage_id: int
    stage_name: str
    is_approvable: bool
    has_section: bool
    status: str
    questions: list[QuestionAnswerPreview]
    sections: list[SectionPreview]
    approval_labels: list[ApprovalLabelPreview]
    columns: list[ColumnPreview] = []

    @classmethod
    def from_dto(cls, dto: ChecklistStagePreviewDTO) -> ChecklistStagePreview:
        return cls(
            format_stage_mapping_id=dto.format_stage_mapping_id,
            stage_id=dto.stage_id,
            stage_name=dto.stage_name,
            is_approvable=dto.is_approvable,
            has_section=dto.has_section,
            status=dto.status,
            questions=[QuestionAnswerPreview.from_dto(q) for q in dto.questions],
            sections=[SectionPreview.from_dto(s) for s in dto.sections],
            approval_labels=[ApprovalLabelPreview.from_dto(a) for a in dto.approval_labels],
            columns=[ColumnPreview.from_dto(c) for c in dto.columns],
        )


class ChecklistPreviewResponse(BaseModel):
    format_id: int
    format_name: str
    format_no: str
    format_type: str
    has_declaration_question: bool
    unit_name: str
    stages: list[ChecklistStagePreview]

    @classmethod
    def from_dto(cls, dto: ChecklistPreviewDTO) -> ChecklistPreviewResponse:
        return cls(
            format_id=dto.format_id,
            format_name=dto.format_name,
            format_no=dto.format_no,
            format_type=dto.format_type,
            has_declaration_question=dto.has_declaration_question,
            unit_name=dto.unit_name,
            stages=[ChecklistStagePreview.from_dto(s) for s in dto.stages],
        )
