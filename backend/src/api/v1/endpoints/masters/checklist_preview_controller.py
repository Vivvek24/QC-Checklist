"""Checklist Preview — API controller (thin).

Parses HTTP, delegates to ChecklistPreviewService, and maps domain errors to
HTTP status codes. No business rules or ORM access here.

Kept in masters/ (not qc_checklist/) since it's a read view over Template
Studio's own aggregates (formats, stages, sections, questions, columns) —
shared by Template Studio's config editor and Create Request's fill-in form,
so both render a format's checklist from one call instead of separate
per-stage lookups.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.masters.checklist_preview_schema import ChecklistPreviewResponse
from src.application.services.masters.checklist_preview_service import ChecklistPreviewService
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.repositories.masters.approval_label_repository_impl import (
    ApprovalLabelRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.format_repository_impl import (
    FormatRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.format_stage_mapping_repository_impl import (  # noqa: E501
    FormatStageMappingRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.question_option_repository_impl import (
    QuestionOptionRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.question_repository_impl import (
    QuestionRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.question_sub_question_repository_impl import (  # noqa: E501
    QuestionSubQuestionRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.section_repository_impl import (
    SectionRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.stage_question_mapping_repository_impl import (  # noqa: E501
    StageQuestionMappingRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.stage_repository_impl import (
    StageRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.template_layout_column_repository_impl import (  # noqa: E501
    TemplateLayoutColumnRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.unit_repository_impl import (
    UnitRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist", tags=["Masters - Checklist Preview"])


def _get_service(session: AsyncSession = Depends(get_db_session)) -> ChecklistPreviewService:
    return ChecklistPreviewService(
        format_repo=FormatRepositoryImpl(session),
        unit_repo=UnitRepositoryImpl(session),
        format_stage_mapping_repo=FormatStageMappingRepositoryImpl(session),
        stage_repo=StageRepositoryImpl(session),
        stage_question_mapping_repo=StageQuestionMappingRepositoryImpl(session),
        question_repo=QuestionRepositoryImpl(session),
        question_option_repo=QuestionOptionRepositoryImpl(session),
        question_sub_question_repo=QuestionSubQuestionRepositoryImpl(session),
        section_repo=SectionRepositoryImpl(session),
        approval_label_repo=ApprovalLabelRepositoryImpl(session),
        column_repo=TemplateLayoutColumnRepositoryImpl(session),
    )


@router.get(
    "/preview",
    response_model=ChecklistPreviewResponse,
    summary="Preview checklist structure (rows + Template Studio columns) for a format",
    dependencies=[Depends(require_api_permission("checklist_requests", "READ"))],
)
async def preview_checklist(
    format_id: int = Query(..., gt=0),
    service: ChecklistPreviewService = Depends(_get_service),
) -> ChecklistPreviewResponse:
    """Returns the full checklist structure in memory for a given format. Nothing is persisted."""
    try:
        dto = await service.get_preview(format_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return ChecklistPreviewResponse.from_dto(dto)
