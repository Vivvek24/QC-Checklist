"""ChecklistRequestDetail — API controller (thin).

One aggregate read endpoint for the fill-next-stage page: returns a request's
full template preview plus every stage's status, answers, sub-answers and
approval mappings in a single response, replacing the page's per-stage request
fan-out. Delegates to ChecklistRequestDetailService, which composes the existing
per-entity services — no business rules or ORM access here.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.qc_checklist.request_detail_schema import (
    ChecklistRequestDetailResponse,
)
from src.application.services.masters.checklist_preview_service import ChecklistPreviewService
from src.application.services.qc_checklist.checklist_stage_service import ChecklistStageService
from src.application.services.qc_checklist.question_answer_service import QuestionAnswerService
from src.application.services.qc_checklist.request_detail_service import (
    ChecklistRequestDetailService,
)
from src.application.services.qc_checklist.stage_approval_label_mapping_service import (
    StageApprovalLabelMappingService,
)
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
from src.infrastructure.database.repositories.masters.sap_field_repository_impl import (
    SapFieldRepositoryImpl,
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
from src.infrastructure.database.repositories.qc_checklist.checklist_request_repository_impl import (  # noqa: E501
    ChecklistRequestRepositoryImpl,
)
from src.infrastructure.database.repositories.qc_checklist.checklist_stage_repository_impl import (
    ChecklistStageRepositoryImpl,
)
from src.infrastructure.database.repositories.qc_checklist.question_answer_repository_impl import (
    QuestionAnswerRepositoryImpl,
)
from src.infrastructure.database.repositories.qc_checklist.stage_approval_label_mapping_repository_impl import (  # noqa: E501
    StageApprovalLabelMappingRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist/requests", tags=["QC Checklist - Request Detail"])


def _get_service(
    session: AsyncSession = Depends(get_db_session),
) -> ChecklistRequestDetailService:
    preview_service = ChecklistPreviewService(
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
        sap_field_repo=SapFieldRepositoryImpl(session),
    )
    return ChecklistRequestDetailService(
        request_repo=ChecklistRequestRepositoryImpl(session),
        preview_service=preview_service,
        stage_service=ChecklistStageService(repo=ChecklistStageRepositoryImpl(session)),
        answer_service=QuestionAnswerService(repo=QuestionAnswerRepositoryImpl(session)),
        approval_mapping_service=StageApprovalLabelMappingService(
            repo=StageApprovalLabelMappingRepositoryImpl(session)
        ),
    )


@router.get(
    "/{request_number}/detail",
    response_model=ChecklistRequestDetailResponse,
    summary="Full request detail (preview + per-stage answers) for the fill page",
    dependencies=[Depends(require_api_permission("checklist_requests", "READ"))],
)
async def get_request_detail(
    request_number: str,
    service: ChecklistRequestDetailService = Depends(_get_service),
) -> ChecklistRequestDetailResponse:
    """One call returning everything the fill-next-stage page needs: the format
    preview tree, each stage's live status, and all saved answers / sub-answers
    / approval mappings. Nothing is persisted."""
    try:
        dto = await service.get_request_detail(request_number)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return ChecklistRequestDetailResponse.from_dto(dto)
