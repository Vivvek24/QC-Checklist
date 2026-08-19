"""Validate Checklist Request — API controller."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.application.services.qc_checklist.validate_checklist_service import ValidateChecklistService
from src.domain.entities.user import User
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist", tags=["QC Checklist - Validation"])


class ValidationErrorSchema(BaseModel):
    stage_id: int
    stage_name: str
    question_id: int | None = None
    question_title: str
    message: str


class ValidateResponse(BaseModel):
    is_valid: bool
    errors: list[ValidationErrorSchema]


class ValidateRequest(BaseModel):
    checklist_request_id: int


@router.post("/validate", response_model=ValidateResponse,
             summary="Validate a checklist request before submission",
             dependencies=[Depends(require_api_permission("checklist_requests", "UPDATE"))])
async def validate_checklist(
    body: ValidateRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> ValidateResponse:
    """
    Validates all question answers for the given checklist request.
    Returns validation errors if any fields are incomplete or invalid.
    """
    service = ValidateChecklistService(session)
    result = await service.validate(body.checklist_request_id)

    return ValidateResponse(
        is_valid=result.is_valid,
        errors=[
            ValidationErrorSchema(
                stage_id=e.stage_id,
                stage_name=e.stage_name,
                question_id=e.question_id,
                question_title=e.question_title,
                message=e.message,
            )
            for e in result.errors
        ],
    )
