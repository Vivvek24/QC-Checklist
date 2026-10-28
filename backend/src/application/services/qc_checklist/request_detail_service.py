"""ChecklistRequestDetail — aggregate application service.

Composes the fill-next-stage read-model for one request in a single pass:
the format preview (reused from ChecklistPreviewService) plus every persisted
stage's status, saved answers, sub-answers and approval mappings (reused from
the per-entity services). Replaces the frontend's per-stage request fan-out
(3 calls per stage) with one aggregate — the services it calls are unchanged.
"""

from src.application.dtos.qc_checklist.request_detail_dtos import (
    ChecklistRequestDetailDTO,
    StageAnswersBlockDTO,
    StageStateDTO,
)
from src.application.services.masters.checklist_preview_service import ChecklistPreviewService
from src.application.services.qc_checklist.checklist_stage_service import ChecklistStageService
from src.application.services.qc_checklist.question_answer_service import QuestionAnswerService
from src.application.services.qc_checklist.stage_approval_label_mapping_service import (
    StageApprovalLabelMappingService,
)
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.domain.repositories.qc_checklist.checklist_request_repository import (
    IChecklistRequestRepository,
)

RECON_FORMAT = "ReconcilationSheet"


class ChecklistRequestDetailService:
    """Builds the one-call fill-page payload by composing existing services."""

    def __init__(
        self,
        request_repo: IChecklistRequestRepository,
        preview_service: ChecklistPreviewService,
        stage_service: ChecklistStageService,
        answer_service: QuestionAnswerService,
        approval_mapping_service: StageApprovalLabelMappingService,
    ) -> None:
        self._request_repo = request_repo
        self._preview_service = preview_service
        self._stage_service = stage_service
        self._answer_service = answer_service
        self._approval_mapping_service = approval_mapping_service

    async def get_request_detail(self, request_number: str) -> ChecklistRequestDetailDTO:
        request = await self._request_repo.get_by_code(request_number)
        if request is None or request.format_id is None:
            raise EntityNotFoundError("ChecklistRequest", request_number)

        format_id = request.format_id
        preview = await self._preview_service.get_preview(format_id)
        stages = await self._stage_service.list_by_checklist_request(request.id)
        question_approvals = await self._approval_mapping_service.list_by_checklist_request(
            request.id
        )

        is_recon = preview.format_type == RECON_FORMAT

        stage_states = [
            StageStateDTO(
                format_stage_mapping_id=s.format_stage_mapping_id,
                checklist_stage_id=s.id,
                status=s.status,
            )
            for s in stages
        ]

        answer_blocks: list[StageAnswersBlockDTO] = []
        for s in stages:
            if not s.status:
                continue
            # 'Initial' is normally a freshly-opened stage with nothing filled —
            # except for a ReconcilationSheet, whose Test stage carries the
            # auto-generated per-test rows while it stays Initial through the
            # supervisor's issuing phase. Mirror the frontend's load gate.
            if s.status == "Initial" and not is_recon:
                continue
            answers = await self._answer_service.list_stage_answers(s.id)
            sub_answers = await self._answer_service.list_sub_answers(s.id)
            approval_mappings = await self._approval_mapping_service.list_by_checklist_stage(s.id)
            answer_blocks.append(
                StageAnswersBlockDTO(
                    format_stage_mapping_id=s.format_stage_mapping_id,
                    checklist_stage_id=s.id,
                    answers=answers,
                    sub_answers=sub_answers,
                    approval_mappings=approval_mappings,
                )
            )

        return ChecklistRequestDetailDTO(
            request_id=request.id,
            request_number=request.request_number,
            format_id=format_id,
            preview=preview,
            stages=stage_states,
            answer_blocks=answer_blocks,
            question_approvals=question_approvals,
        )
