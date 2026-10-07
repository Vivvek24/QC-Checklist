"""Submit Stage — Pydantic schemas.

Each schema owns its own translation to/from the application layer's
dataclasses (to_dto / from_dto) so the controller stays a pure HTTP layer:
parse the request, call the service, translate the result — no field-by-field
mapping or payload-building there.
"""

from pydantic import BaseModel

from src.application.services.qc_checklist.submit_stage_service import (
    ExtraStagePayload,
    QuestionAnswerPayload,
    SubmitStageRequest,
    SubmitStageResult,
)


class AnswerSchema(BaseModel):
    stage_question_mapping_id: int
    question_id: int
    textbox_value: str = ""
    question_option_id: int | None = None
    response_question_option_id: int | None = None
    response_answer: str = ""
    product_id: int | None = None
    date_time: str | None = None
    helpers: list[str] | None = None

    def to_payload(self) -> QuestionAnswerPayload:
        return QuestionAnswerPayload(
            stage_question_mapping_id=self.stage_question_mapping_id,
            question_id=self.question_id,
            textbox_value=self.textbox_value,
            question_option_id=self.question_option_id,
            response_question_option_id=self.response_question_option_id,
            response_answer=self.response_answer,
            product_id=self.product_id,
            date_time=self.date_time,
            helpers=self.helpers,
        )


class ExtraStageSchema(BaseModel):
    """A secondary stage (e.g. Basic Details) submitted with the primary one."""
    format_stage_mapping_id: int
    checklist_stage_id: int | None = None
    answers: list[AnswerSchema] = []

    def to_payload(self) -> ExtraStagePayload:
        return ExtraStagePayload(
            format_stage_mapping_id=self.format_stage_mapping_id,
            checklist_stage_id=self.checklist_stage_id,
            answers=[a.to_payload() for a in self.answers] if self.answers else None,
        )


class SubmitStageRequestSchema(BaseModel):
    checklist_request_id: int | None = None
    format_id: int
    checklist_stage_id: int | None = None
    format_stage_mapping_id: int
    action: str  # submit, save_draft, approve, refer_back
    remark_id: int | None = None
    remark_text: str = ""
    answers: list[AnswerSchema] = []
    # Secondary stages persisted + advanced to Pending together with the
    # primary stage on first submit (used for Basic Details).
    extra_stages: list[ExtraStageSchema] = []

    def to_dto(self) -> SubmitStageRequest:
        return SubmitStageRequest(
            checklist_request_id=self.checklist_request_id,
            format_id=self.format_id,
            checklist_stage_id=self.checklist_stage_id,
            format_stage_mapping_id=self.format_stage_mapping_id,
            action=self.action,
            remark_id=self.remark_id,
            remark_text=self.remark_text,
            answers=[a.to_payload() for a in self.answers] if self.answers else None,
            extra_stages=[e.to_payload() for e in self.extra_stages] if self.extra_stages else None,
        )


class SubmitStageResponseSchema(BaseModel):
    success: bool
    checklist_request_id: int
    checklist_stage_id: int
    new_status: str
    message: str

    @classmethod
    def from_dto(cls, result: SubmitStageResult) -> "SubmitStageResponseSchema":
        return cls(
            success=result.success,
            checklist_request_id=result.checklist_request_id,
            checklist_stage_id=result.checklist_stage_id,
            new_status=result.new_status,
            message=result.message,
        )
