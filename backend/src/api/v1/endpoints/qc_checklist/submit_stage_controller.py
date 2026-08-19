"""Submit Stage — API controller for submitting/saving/approving/referring back a checklist stage."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.application.services.qc_checklist.submit_stage_service import (
    SubmitStageService,
    SubmitStageRequest,
    QuestionAnswerPayload,
)
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.models.role_model import RoleAssignmentModel
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission
from sqlalchemy import select

router = APIRouter(prefix="/qc-checklist", tags=["QC Checklist - Submit Stage"])


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


class SubmitStageRequestSchema(BaseModel):
    checklist_request_id: int | None = None
    format_id: int
    checklist_stage_id: int | None = None
    format_stage_mapping_id: int
    action: str  # submit, save_draft, approve, refer_back
    remark_id: int | None = None
    remark_text: str = ""
    answers: list[AnswerSchema] = []


class SubmitStageResponseSchema(BaseModel):
    success: bool
    checklist_request_id: int
    checklist_stage_id: int
    new_status: str
    message: str


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
    - approve: Approve the stage (opens next stage)
    - refer_back: Send the stage back to the filling analyst
    """
    # Get user's role
    ra_result = await session.execute(
        select(RoleAssignmentModel.role_id).where(
            RoleAssignmentModel.user_id == current_user.id,
            RoleAssignmentModel.is_active.is_(True),
        ).limit(1)
    )
    role_id = ra_result.scalar_one_or_none()

    service = SubmitStageService(session)

    request = SubmitStageRequest(
        checklist_request_id=body.checklist_request_id,
        format_id=body.format_id,
        checklist_stage_id=body.checklist_stage_id,
        format_stage_mapping_id=body.format_stage_mapping_id,
        action=body.action,
        remark_id=body.remark_id,
        remark_text=body.remark_text,
        answers=[
            QuestionAnswerPayload(
                stage_question_mapping_id=a.stage_question_mapping_id,
                question_id=a.question_id,
                textbox_value=a.textbox_value,
                question_option_id=a.question_option_id,
                response_question_option_id=a.response_question_option_id,
                response_answer=a.response_answer,
                product_id=a.product_id,
                date_time=a.date_time,
                helpers=a.helpers,
            )
            for a in body.answers
        ] if body.answers else None,
    )

    try:
        result = await service.execute(request, user_id=current_user.id, role_id=role_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    await session.commit()

    return SubmitStageResponseSchema(
        success=result.success,
        checklist_request_id=result.checklist_request_id,
        checklist_stage_id=result.checklist_stage_id,
        new_status=result.new_status,
        message=result.message,
    )
