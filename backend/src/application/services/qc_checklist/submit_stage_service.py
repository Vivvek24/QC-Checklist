"""Submit action — send a filled stage for approval.

Validates the stage, advances it to Pending, records the initiator's approval
action, and (on first submit) also persists + advances any secondary stages
(e.g. Basic Details) that ride along. Handles the refer-back resubmit case by
reopening the approver's refer-back mapping so the chain continues.

Re-exports the shared DTOs so existing imports of this module keep working.
"""

from datetime import UTC, datetime

from sqlalchemy import select

from src.application.services.qc_checklist.stage_action_base_service import (
    ExtraStagePayload,
    QuestionAnswerPayload,
    StageActionBase,
    SubmitStageRequest,
    SubmitStageResult,
)
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
    "ExtraStagePayload",
]


class SubmitStageService(StageActionBase):
    async def execute(
        self, request: SubmitStageRequest, user_id: int, role_id: int | None,
    ) -> SubmitStageResult:
        now = datetime.now(UTC)
        resolved = await self.resolve(request, user_id, role_id, now, authorize=True)
        cr, cs = resolved.request, resolved.stage

        # Basic Details rides along on first submit (no Submit button of its own).
        if request.extra_stages:
            await self._submit_extra_stages(cr, request.extra_stages, user_id, now)

        return await self._submit(
            cr, cs, user_id, role_id, request.remark_id, request.remark_text, now
        )

    async def _submit(
        self, cr: ChecklistRequestModel, cs: ChecklistStageModel, user_id: int, role_id: int | None,
        remark_id, remark_text, now: datetime,
    ) -> SubmitStageResult:
        # Validate the stage being submitted — blocks on failure.
        await self._validate_stage(cr, cs)
        format_type = await self._get_format_type(cr.format_id)

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
        user_id: int, now: datetime,
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

            if extra.answers:
                await self._persist_answers(cs.id, extra.answers, user_id, now)

            await self._validate_stage(cr, cs)

            if cs.status in ("Initial", "Draft", "", "Saved", "SaveAsDraft"):
                cs.status = "Pending"
            cs.user_id = user_id
            cs.modified_by = str(user_id)
            cs.modified_date = now

        await self._session.flush()
