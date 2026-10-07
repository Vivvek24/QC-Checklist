"""Save-draft action — persist a stage's answers without submitting it.

Only the filling analyst sees a draft; it is not sent for approval, so there
is no validation or role gate here (that applies to submit/approve/refer-back).
"""

from datetime import UTC, datetime

from src.application.services.qc_checklist.stage_action_base_service import (
    StageActionBase,
    SubmitStageRequest,
    SubmitStageResult,
)


class SaveDraftService(StageActionBase):
    async def execute(
        self, request: SubmitStageRequest, user_id: int, role_id: int | None,
    ) -> SubmitStageResult:
        now = datetime.now(UTC)
        resolved = await self.resolve(request, user_id, role_id, now, authorize=False)
        cr, cs = resolved.request, resolved.stage

        cs.status = "Draft"
        cs.modified_by = str(user_id)
        cs.modified_date = now
        cr.status = "Draft"
        cr.modified_by = str(user_id)
        cr.modified_date = now
        await self._session.flush()

        return SubmitStageResult(
            success=True,
            checklist_request_id=cr.id,
            checklist_stage_id=cs.id,
            new_status="Draft",
            message="Saved as draft successfully.",
        )
