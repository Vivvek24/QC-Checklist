"""Submit action — send a filled stage for approval.

Validates the stage, advances it to Pending, records the initiator's approval
action, and (on first submit) also persists + advances any secondary stages
(e.g. Basic Details) that ride along. Handles the refer-back resubmit case by
reopening the approver's refer-back mapping so the chain continues.

Re-exports the shared DTOs so existing imports of this module keep working.
"""

from datetime import UTC, datetime

from sqlalchemy import select

from src.application.dtos.qc_checklist.stage_action_dtos import (
    ExtraStagePayload,
    QuestionAnswerPayload,

    QuestionApprovalPayload,
    SubmitStageRequest,
    SubmitStageResult,
)
from src.application.services.qc_checklist.stage_action_base_service import StageActionBase
from src.infrastructure.database.models.qc_checklist.checklist_request_model import (
    ChecklistRequestModel,
)
from src.infrastructure.database.models.qc_checklist.checklist_stage_model import (
    ChecklistStageModel,
)

__all__ = [
    "SubmitStageService",
    "SubmitStageRequest",
    "SubmitStageResult",
    "QuestionAnswerPayload",
    "QuestionApprovalPayload",
    "ExtraStagePayload",
]


class SubmitStageService(StageActionBase):
    async def execute(
        self, request: SubmitStageRequest, user_id: int, role_id: int | None,
    ) -> SubmitStageResult:
        now = datetime.now(UTC)
        resolved = await self.resolve(request, user_id, role_id, now, authorize=True)
        cr, cs = resolved.request, resolved.stage

        # Per-question approval remarks for the primary stage's approvable
        # questions (answers were just saved in resolve()).
        await self._persist_question_approvals(
            cs.id, request.question_approvals, user_id, role_id, now
        )

        # Basic Details rides along on first submit (no Submit button of its own).
        if request.extra_stages:
            await self._submit_extra_stages(cr, request.extra_stages, user_id, role_id, now)

        return await self._submit(
            cr, cs, user_id, role_id, request.remark_id, request.remark_text, now
        )

    async def _submit(
        self, cr: ChecklistRequestModel, cs: ChecklistStageModel, user_id: int, role_id: int | None,
        remark_id, remark_text, now: datetime,
    ) -> SubmitStageResult:
        format_type = await self._get_format_type(cr.format_id)

        # ReconcilationSheet — supervisor's vial-issuing pass. The supervisor's
        # Submit only commits the vials issued so far: the stage stays Initial,
        # NO approval action is recorded and NO remark is persisted.
        #
        # This covers BOTH the intermediate submits (vials still unissued) AND
        # the FINAL supervisor submit that issues the last vial (now all issued,
        # but the actor is still the supervisor — the APPROVE-label role, NOT the
        # SUBMIT-label/analyst). Only the analyst's own submit (SUBMIT-label role)
        # falls through to record the remark + advance the stage to Pending.
        is_supervisor_issuing = format_type == "ReconcilationSheet" and (
            await self._has_unissued_vials(cs)
            or not await self._is_submit_label_role(cs, role_id)
        )
        if is_supervisor_issuing:
            # Keep the Test stage Initial (the supervisor can act again). The
            # REQUEST is in flight but NOT yet Pending — the request only goes
            # Pending on the analyst's final submit (all vials issued). While
            # the supervisor is still issuing, mark the request InProgress.
            cs.user_id = user_id
            cs.modified_by = str(user_id)
            cs.modified_date = now
            cr.status = "InProgress"
            cr.modified_by = str(user_id)
            cr.modified_date = now
            await self._update_status_format(cr, format_type)
            await self._session.flush()
            return SubmitStageResult(
                success=True,
                checklist_request_id=cr.id,
                checklist_stage_id=cs.id,
                new_status="Initial",
                message="Vials issued. Stage remains open until all vials are issued.",
            )

        # Validate the stage being submitted — blocks on failure.
        await self._validate_stage(cr, cs)

        # Resubmit of a referred-back stage: reopen the approver's refer-back
        # mapping so they can act again; update the initiator's mapping in place.
        was_refer_back = cs.status == "ReferBack"
        if was_refer_back:
            await self._reset_refer_back_mappings(cs)

        cs.status = "Pending"
        cs.user_id = user_id
        cs.submit_remarks = remark_text
        cs.modified_by = str(user_id)
        cs.modified_date = now

        if was_refer_back:
            await self._update_initiator_mapping(
                cs, user_id, role_id, remark_id, remark_text, now
            )
        else:
            await self._record_approval_action(
                cs, user_id, role_id, remark_id, remark_text, now
            )

        # ReconcilationSheet: this is the analyst's final submit (all vials
        # issued). Stamp the Basic Details "EndDate" (Analysis Completion Date)
        # with the current date/time.
        if format_type == "ReconcilationSheet":
            await self._populate_end_date(cr, user_id, now)

        cr.status = "Pending"
        cr.modified_by = str(user_id)
        cr.modified_date = now
        await self._update_status_format(cr, format_type)

        await self._session.flush()
        return SubmitStageResult(
            success=True,
            checklist_request_id=cr.id,
            checklist_stage_id=cs.id,
            new_status="Pending",
            message="Stage submitted successfully.",
        )

    async def _submit_extra_stages(
        self, cr: ChecklistRequestModel, extra_stages: list[ExtraStagePayload],
        user_id: int, role_id: int | None, now: datetime,
    ) -> None:
        """Persist + advance secondary stages (Basic Details) submitted with the
        primary one. Validates each; blocks the whole submit if invalid."""
        for extra in extra_stages:
            cs = None
            if extra.checklist_stage_id:
                cs_result = await self._session.execute(
                    select(ChecklistStageModel).where(
                        ChecklistStageModel.id == extra.checklist_stage_id
                    )
                )
                cs = cs_result.scalar_one_or_none()
            if cs is None:
                fsm_id = extra.format_stage_mapping_id
                cs_result = await self._session.execute(
                    select(ChecklistStageModel).where(
                        ChecklistStageModel.checklist_request_id == cr.id,
                        ChecklistStageModel.format_stage_mapping_id == fsm_id,
                    )
                )
                cs = cs_result.scalar_one_or_none()
            if cs is None:
                continue

            # Whether this is Basic Details' FIRST submit (it was still
            # fillable). On a recon analyst-phase ride-along Basic Details is
            # already Pending — we must NOT re-expand product tests then, or the
            # Test stage's issued-vial rows (is_issued_vails / received_by_date /
            # issuer_name) would be wiped and recreated.
            first_submit = cs.status in ("Initial", "Draft", "", "Saved", "SaveAsDraft")

            if extra.answers:
                await self._persist_answers(cs.id, extra.answers, user_id, now)

            # Per-question approvals for this extra stage's approvable questions.
            await self._persist_question_approvals(
                cs.id, extra.question_approvals, user_id, role_id, now
            )

            if first_submit:
                # Expand any product chosen on this stage (Masters question) into
                # one test row per product test on the next stage. Only on the
                # first submit — re-running later would destroy issued vials.
                await self._expand_product_tests(cr, cs, user_id, now)

                # Stamp the "StartDate" custom-answer question with the submit
                # time (analysis start date).
                await self._populate_start_date(cs, user_id, now)

            await self._validate_stage(cr, cs)

            if first_submit:
                cs.status = "Pending"
            cs.user_id = user_id
            cs.modified_by = str(user_id)
            cs.modified_date = now

        await self._session.flush()
