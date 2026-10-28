"""ChecklistRequestDetail — aggregate application DTOs.

The read-model for the fill-next-stage page: a request's full template preview
plus every stage's live status, saved answers, sub-answers and approval
mappings — assembled once so the page loads from a single call instead of a
per-stage request fan-out. Composed of the existing per-entity DTOs; this layer
only groups them, it does not redeclare their fields.
"""

from dataclasses import dataclass, field

from src.application.dtos.masters.checklist_preview_dtos import ChecklistPreviewDTO
from src.application.dtos.qc_checklist.question_answer_dtos import (
    ParentSubAnswersDTO,
    StageAnswerDTO,
)
from src.application.dtos.qc_checklist.stage_approval_label_mapping_dtos import (
    StageApprovalLabelMappingDTO,
)


@dataclass(frozen=True)
class StageStateDTO:
    """One persisted stage's identity + live status, keyed by its format stage
    mapping (so the frontend can map the preview tree to the real stage id)."""
    format_stage_mapping_id: int | None
    checklist_stage_id: int
    status: str


@dataclass(frozen=True)
class StageAnswersBlockDTO:
    """All saved data for one stage, grouped under its format stage mapping:
    the stage's answers, grouped sub-answers, and stage-level approval
    mappings."""
    format_stage_mapping_id: int | None
    checklist_stage_id: int
    answers: list[StageAnswerDTO] = field(default_factory=list)
    sub_answers: list[ParentSubAnswersDTO] = field(default_factory=list)
    approval_mappings: list[StageApprovalLabelMappingDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ChecklistRequestDetailDTO:
    """The complete fill-page read-model for one request."""
    request_id: int
    request_number: str
    format_id: int
    preview: ChecklistPreviewDTO
    stages: list[StageStateDTO]
    answer_blocks: list[StageAnswersBlockDTO]
    # Per-question approval mappings for the whole request (keyed by
    # question_answer_id on the frontend), loaded once for the request.
    question_approvals: list[StageApprovalLabelMappingDTO]
