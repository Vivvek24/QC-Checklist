"""ChecklistRequestDetail — aggregate response schema for the fill page.

Nests the existing per-entity schemas (preview, question answers, sub-answers,
approval mappings) rather than redeclaring their fields, so a field added to any
of them flows through here automatically. Each schema owns its from_dto mapping,
keeping the controller a pure HTTP layer.
"""

from __future__ import annotations

from pydantic import BaseModel

from src.api.v1.schemas.masters.checklist_preview_schema import ChecklistPreviewResponse
from src.api.v1.schemas.qc_checklist.question_answer_schema import (
    ParentSubAnswers,
    QuestionAnswerResponse,
    SubAnswerItem,
)
from src.api.v1.schemas.qc_checklist.stage_approval_label_mapping_schema import (
    StageApprovalLabelMappingResponse,
)
from src.application.dtos.qc_checklist.question_answer_dtos import (
    ParentSubAnswersDTO,
    StageAnswerDTO,
)
from src.application.dtos.qc_checklist.request_detail_dtos import (
    ChecklistRequestDetailDTO,
    StageAnswersBlockDTO,
    StageStateDTO,
)
from src.application.dtos.qc_checklist.stage_approval_label_mapping_dtos import (
    StageApprovalLabelMappingDTO,
)


def _answer_from_dto(dto: StageAnswerDTO) -> QuestionAnswerResponse:
    return QuestionAnswerResponse(**{**vars(dto), "helpers": list(dto.helpers)})


def _sub_answers_from_dto(dto: ParentSubAnswersDTO) -> ParentSubAnswers:
    return ParentSubAnswers(
        parent_question_id=dto.parent_question_id,
        sub_answers=[SubAnswerItem(**vars(s)) for s in dto.sub_answers],
    )


def _mapping_from_dto(dto: StageApprovalLabelMappingDTO) -> StageApprovalLabelMappingResponse:
    return StageApprovalLabelMappingResponse(**dto.__dict__)


class StageState(BaseModel):
    """A persisted stage's identity + live status (keyed by format stage
    mapping so the frontend can overlay it onto the preview tree)."""
    format_stage_mapping_id: int | None
    checklist_stage_id: int
    status: str

    @classmethod
    def from_dto(cls, dto: StageStateDTO) -> StageState:
        return cls(
            format_stage_mapping_id=dto.format_stage_mapping_id,
            checklist_stage_id=dto.checklist_stage_id,
            status=dto.status,
        )


class StageAnswersBlock(BaseModel):
    """All saved data for one stage, grouped under its format stage mapping."""
    format_stage_mapping_id: int | None
    checklist_stage_id: int
    answers: list[QuestionAnswerResponse] = []
    sub_answers: list[ParentSubAnswers] = []
    approval_mappings: list[StageApprovalLabelMappingResponse] = []

    @classmethod
    def from_dto(cls, dto: StageAnswersBlockDTO) -> StageAnswersBlock:
        return cls(
            format_stage_mapping_id=dto.format_stage_mapping_id,
            checklist_stage_id=dto.checklist_stage_id,
            answers=[_answer_from_dto(a) for a in dto.answers],
            sub_answers=[_sub_answers_from_dto(s) for s in dto.sub_answers],
            approval_mappings=[_mapping_from_dto(m) for m in dto.approval_mappings],
        )


class ChecklistRequestDetailResponse(BaseModel):
    """The complete fill-page read-model for one request in a single payload."""
    request_id: int
    request_number: str
    format_id: int
    preview: ChecklistPreviewResponse
    stages: list[StageState]
    answer_blocks: list[StageAnswersBlock]
    question_approvals: list[StageApprovalLabelMappingResponse] = []

    @classmethod
    def from_dto(cls, dto: ChecklistRequestDetailDTO) -> ChecklistRequestDetailResponse:
        return cls(
            request_id=dto.request_id,
            request_number=dto.request_number,
            format_id=dto.format_id,
            preview=ChecklistPreviewResponse.from_dto(dto.preview),
            stages=[StageState.from_dto(s) for s in dto.stages],
            answer_blocks=[StageAnswersBlock.from_dto(b) for b in dto.answer_blocks],
            question_approvals=[_mapping_from_dto(m) for m in dto.question_approvals],
        )
