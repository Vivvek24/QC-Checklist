"""Stage action — application DTOs.

Input payloads and the result shape for the checklist stage lifecycle
(submit / save-draft / approve / refer-back). These are transport/boundary
DTOs the controller translates to from its request schema and the services
consume — they are NOT domain entities, so they live in the application DTO
layer (not domain/entities, which must stay free of transport concerns).
"""

from dataclasses import dataclass


@dataclass
class SubAnswerPayload:
    """A sub-question's answer. Persisted as its own QuestionAnswer row and
    linked to the parent answer via question_answer_sub_question_answers."""
    question_id: int
    textbox_value: str = ""
    question_option_id: int | None = None
    response_question_option_id: int | None = None
    response_answer: str = ""


@dataclass
class QuestionAnswerPayload:
    """Payload for a single question answer."""
    stage_question_mapping_id: int
    question_id: int
    textbox_value: str = ""
    question_option_id: int | None = None
    response_question_option_id: int | None = None
    response_answer: str = ""
    product_id: int | None = None
    date_time: str | None = None
    helpers: list[str] | None = None
    # Calculated-question accumulation: the parent textbox is cleared, the
    # values live in helpers, and the running total rides here.
    has_helper: bool = False
    answer_total_vails: int = 0
    sub_answers: list[SubAnswerPayload] | None = None


@dataclass
class QuestionApprovalPayload:
    """A per-question approval-label remark pick (mirrors a stage approval
    remark, but tied to one filled question). Persisted into
    stage_approval_label_mappings keyed by question_answer_id."""
    stage_question_mapping_id: int
    approval_label_id: int
    remark_id: int | None = None
    remark_text: str = ""


@dataclass
class ExtraStagePayload:
    """A secondary stage submitted alongside the primary one (e.g. Basic
    Details, which has no Submit button of its own)."""
    format_stage_mapping_id: int
    checklist_stage_id: int | None = None
    answers: list[QuestionAnswerPayload] | None = None
    question_approvals: list[QuestionApprovalPayload] | None = None


@dataclass
class SubmitStageRequest:
    """Input for any stage action."""
    checklist_request_id: int | None  # None for first-time creation
    format_id: int
    checklist_stage_id: int | None  # None for first-time creation
    format_stage_mapping_id: int
    action: str  # submit, save_draft, approve, refer_back
    remark_id: int | None = None
    remark_text: str = ""
    answers: list[QuestionAnswerPayload] | None = None
    extra_stages: list[ExtraStagePayload] | None = None
    # Per-question approval remark picks for the PRIMARY stage's approvable
    # questions (keyed to question_answer_id once answers are saved).
    question_approvals: list[QuestionApprovalPayload] | None = None


@dataclass
class SubmitStageResult:
    """Output after a stage action."""
    success: bool
    checklist_request_id: int
    checklist_stage_id: int
    new_status: str
    message: str
