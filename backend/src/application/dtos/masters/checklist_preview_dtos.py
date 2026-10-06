"""Checklist Preview — application DTOs.

Shapes returned by ChecklistPreviewService.get_preview: the full
format -> stages -> sections -> questions tree used to render (not persist)
a checklist, plus each stage/section's Template Studio column layout so both
Template Studio (the config editor) and Create Request (the fill-in form)
can render from one shared call.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QuestionOptionPreviewDTO:
    id: int
    label: str


@dataclass(frozen=True)
class QuestionAnswerPreviewDTO:
    stage_question_mapping_id: int
    question_id: int
    question_title: str
    serial_number: int
    section_id: int | None
    section_name: str | None
    show_on_grid: bool
    answer_type: str
    has_text_box: bool
    has_multiple_text_box: bool
    has_sub_question: bool
    is_declaration_question: bool
    aql_limit: str
    # Edit-only mapping attributes — carried so Template Studio can hydrate
    # its design canvas from this one preview call (no separate
    # stage-question-mappings fetch). The fill-in flow ignores these.
    sap_field_id: int | None
    is_editable: bool
    custom_answers: str | None
    sub_questions: list["QuestionAnswerPreviewDTO"] = field(default_factory=list)
    options: list[QuestionOptionPreviewDTO] = field(default_factory=list)
    response_options: list[QuestionOptionPreviewDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ApprovalLabelPreviewDTO:
    approval_label_id: int
    label: str


@dataclass(frozen=True)
class ColumnPreviewDTO:
    """A single Template Studio column, as read for rendering (not editing)."""

    id: int
    header: str
    column_type: str
    display_order: int
    width: str | None
    is_required: bool


@dataclass(frozen=True)
class SectionPreviewDTO:
    section_id: int
    section_name: str
    questions: list[QuestionAnswerPreviewDTO] = field(default_factory=list)
    columns: list[ColumnPreviewDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ChecklistStagePreviewDTO:
    format_stage_mapping_id: int
    stage_id: int
    stage_name: str
    is_approvable: bool
    has_section: bool
    status: str
    questions: list[QuestionAnswerPreviewDTO] = field(default_factory=list)
    sections: list[SectionPreviewDTO] = field(default_factory=list)
    approval_labels: list[ApprovalLabelPreviewDTO] = field(default_factory=list)
    columns: list[ColumnPreviewDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ChecklistPreviewDTO:
    format_id: int
    format_name: str
    format_no: str
    format_type: str
    has_declaration_question: bool
    unit_name: str
    stages: list[ChecklistStagePreviewDTO] = field(default_factory=list)
