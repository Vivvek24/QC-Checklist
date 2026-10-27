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
    master_type: str | None
    has_text_box: bool
    has_multiple_text_box: bool
    has_sub_question: bool
    is_declaration_question: bool
    aql_limit: str
    # Edit-only mapping attributes — carried so Template Studio can hydrate
    # its design canvas from this one preview call (no separate
    # stage-question-mappings fetch). The fill-in flow ignores these.
    sap_field_id: int | None
    sap_field_name: str | None
    is_editable: bool
    custom_answers: str | None
    # When the question is approvable, the approval labels configured for it
    # (same shape as a stage's labels) so the grid can render a per-question
    # approval block under it.
    is_approvable: bool = False
    # When true, picking a product (Masters answer) on the same stage auto-fills
    # this question's answer with the product's storage_conditions.
    has_associated_master: bool = False
    # When true, the "+ Add" helper button runs the calculated-answer flow
    # (positive-integer validation + running total; see TemplateCell).
    is_calculated: bool = False
    sub_questions: list["QuestionAnswerPreviewDTO"] = field(default_factory=list)
    options: list[QuestionOptionPreviewDTO] = field(default_factory=list)
    response_options: list[QuestionOptionPreviewDTO] = field(default_factory=list)
    approval_labels: list["ApprovalLabelPreviewDTO"] = field(default_factory=list)


@dataclass(frozen=True)
class ApprovalLabelPreviewDTO:
    approval_label_id: int
    label: str
    # Roles configured to act on this label (used by the fill grid to gate who
    # can pick the per-question remark). Empty for stage labels (not needed there).
    role_ids: list[int] = field(default_factory=list)


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
    # The stage's declaration-grid column layout (rendered in ApprovalSnip).
    declaration_columns: list[ColumnPreviewDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ChecklistPreviewDTO:
    format_id: int
    format_name: str
    format_no: str
    format_type: str
    has_declaration_question: bool
    unit_name: str
    stages: list[ChecklistStagePreviewDTO] = field(default_factory=list)
