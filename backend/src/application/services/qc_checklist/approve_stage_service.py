"""Approve action — approve a submitted stage.

Validates, marks the stage Approved, records the approver's action, and opens
the next stage. If there is no next stage this is the FINAL approval: the whole
request is marked Approved and any still-Pending stages (notably Basic Details,
the request header) are approved too.
"""

from datetime import UTC, datetime

from src.application.services.qc_checklist.stage_action_base_service import (
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


class ApproveStageService(StageActionBase):
    async def execute(
        self, request: SubmitStageRequest, user_id: int, role_id: int | None,
    ) -> SubmitStageResult:
        now = datetime.now(UTC)
        resolved = await self.resolve(request, user_id, role_id, now, authorize=True)
        cr, cs = resolved.request, resolved.stage
        return await self._approve(
            cr, cs, user_id, role_id, request.remark_id, request.remark_text, now
        )

    async def _approve(
        self, cr: ChecklistRequestModel, cs: ChecklistStageModel, user_id: int, role_id: int | None,
        remark_id, remark_text, now: datetime,
    ) -> SubmitStageResult:
        await self._validate_stage(cr, cs)

        cs.status = "Approved"
        cs.approved_remark = remark_text
        cs.modified_by = str(user_id)
        cs.modified_date = now

        await self._record_approval_action(cs, user_id, role_id, remark_id, remark_text, now)

        next_opened = await self._open_next_stage(cr, cs, user_id, now)
        if not next_opened:
            # Final approval — the whole request is approved.
            cr.is_last_stage = True
            cr.status = "Approved"
            await self._approve_pending_stages(cr, user_id, now)
        else:
            cr.status = "Pending"
        cr.modified_by = str(user_id)
        cr.modified_date = now

        format_type = await self._get_format_type(cr.format_id)
        await self._update_status_format(cr, format_type)

        await self._session.flush()
        return SubmitStageResult(
            success=True,
            checklist_request_id=cr.id,
            checklist_stage_id=cs.id,
            new_status="Approved",
            message="Stage approved successfully."
            + (" Request fully approved." if not next_opened else ""),
        )
