"""Refer-back action — send a submitted stage back to the filling analyst.

The stage goes to ReferBack (only the original user can edit it), but the
request stays Pending — the request as a whole is still in progress, just this
one stage is back with the analyst.
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


class ReferBackService(StageActionBase):
    async def execute(
        self, request: SubmitStageRequest, user_id: int, role_id: int | None,
    ) -> SubmitStageResult:
        now = datetime.now(UTC)
        resolved = await self.resolve(request, user_id, role_id, now, authorize=True)
        cr, cs = resolved.request, resolved.stage
        return await self._refer_back(
            cr, cs, user_id, role_id, request.remark_id, request.remark_text, now
        )

    async def _refer_back(
        self, cr: ChecklistRequestModel, cs: ChecklistStageModel, user_id: int, role_id: int | None,
        remark_id, remark_text, now: datetime,
    ) -> SubmitStageResult:
        cs.status = "ReferBack"
        cs.modified_by = str(user_id)
        cs.modified_date = now
        cr.status = "Pending"
        cr.modified_by = str(user_id)
        cr.modified_date = now

        await self._record_approval_action(
            cs, user_id, role_id, remark_id, remark_text, now, is_refer_back=True
        )

        format_type = await self._get_format_type(cr.format_id)
        await self._update_status_format(cr, format_type)

        await self._session.flush()
        return SubmitStageResult(
            success=True,
            checklist_request_id=cr.id,
            checklist_stage_id=cs.id,
            new_status="ReferBack",
            message="Stage referred back.",
        )
