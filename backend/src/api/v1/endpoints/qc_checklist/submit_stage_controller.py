"""Submit Stage — API controller (thin).

Parses HTTP, resolves the caller's role, picks the focused service for the
requested action (submit / save-draft / approve / refer-back), and maps domain
errors to HTTP status codes. Request/response ↔ DTO translation lives on the
schemas. No business rules, ORM access, or commit here — get_db_session commits
once per request.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.submit_stage_schema import (
    SubmitStageRequestSchema,
    SubmitStageResponseSchema,
)
from src.application.services.qc_checklist.approve_stage_service import ApproveStageService
from src.application.services.qc_checklist.refer_back_service import ReferBackService
from src.application.services.qc_checklist.save_draft_service import SaveDraftService
from src.application.services.qc_checklist.stage_action_base_service import StageActionBase
from src.application.services.qc_checklist.submit_stage_service import SubmitStageService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist", tags=["QC Checklist - Submit Stage"])

# Each action has its own focused service.
_SERVICE_BY_ACTION: dict[str, type[StageActionBase]] = {
    "save_draft": SaveDraftService,
    "submit": SubmitStageService,
    "approve": ApproveStageService,
    "refer_back": ReferBackService,
}


@router.post("/submit-stage", response_model=SubmitStageResponseSchema,
             summary="Submit, save draft, approve, or refer back a checklist stage",
             dependencies=[Depends(require_api_permission("checklist_requests", "UPDATE"))])
async def submit_stage(
    body: SubmitStageRequestSchema,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> SubmitStageResponseSchema:
    """
    Handles all stage lifecycle actions:
    - save_draft: Save answers without submitting
    - submit: Submit the stage for approval
    - approve: Approve the stage (opens next stage, or finalizes the request)
    - refer_back: Send the stage back to the filling analyst
    """
    service_cls = _SERVICE_BY_ACTION.get(body.action)
    if service_cls is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Invalid action: {body.action}")

    service = service_cls(session)
    role_id = await service.resolve_active_role_id(current_user.id)
    try:
        result = await service.execute(body.to_dto(), user_id=current_user.id, role_id=role_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return SubmitStageResponseSchema.from_dto(result)
