"""Template Stage Save — API controller (thin).

Parses HTTP, delegates to TemplateStageSaveService, and maps domain errors to
HTTP status codes. No business rules or ORM access here.

Kept separate from template_controller.py: that controller owns the
Template/TemplateLayoutColumn CRUD surface, while this one owns the single
"save a whole stage atomically" operation, which coordinates three different
aggregates (stage_question_mappings, sections, template_layout_columns) in
one transaction — a distinct enough concern to warrant its own file.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.template_stage_save_schema import (
    TemplateStageSaveRequest,
    TemplateStageSaveResponse,
)
from src.application.services.masters.format_stage_mapping_service import (
    FormatStageMappingService,
)
from src.application.services.masters.template_service import TemplateService
from src.application.services.masters.template_stage_save_service import (
    TemplateStageSaveService,
)
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import BusinessRuleViolationError, DuplicateEntityError
from src.infrastructure.database.repositories.masters.format_stage_mapping_repository_impl import (  # noqa: E501
    FormatStageMappingRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.section_repository_impl import (
    SectionRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.stage_question_mapping_repository_impl import (  # noqa: E501
    StageQuestionMappingRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.template_layout_column_repository_impl import (  # noqa: E501
    TemplateLayoutColumnRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.template_repository_impl import (
    TemplateRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/templates/stages", tags=["Template Stage Save"])
RESOURCE = "templates"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> TemplateStageSaveService:
    # All three repositories share this one request-scoped session, so every
    # write below (rows, sections, columns) participates in the same
    # transaction — get_db_session commits once at the end, or rolls back
    # everything if the service raises.
    return TemplateStageSaveService(
        mapping_repo=StageQuestionMappingRepositoryImpl(session),
        section_repo=SectionRepositoryImpl(session),
        template_service=TemplateService(
            template_repo=TemplateRepositoryImpl(session),
            column_repo=TemplateLayoutColumnRepositoryImpl(session),
        ),
        format_stage_mapping_service=FormatStageMappingService(
            repo=FormatStageMappingRepositoryImpl(session)
        ),
    )


@router.put(
    "/save",
    response_model=TemplateStageSaveResponse,
    summary="Atomically save a stage's rows, columns and sections in one transaction",
    dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))],
)
async def save_stage(
    request: TemplateStageSaveRequest,
    current_user: User = Depends(get_current_active_user),
    service: TemplateStageSaveService = Depends(_get_service),
) -> TemplateStageSaveResponse:
    """Save a stage's configuration. `stage_id` identifies the stage from the
    Stage master; if this format+stage has no format_stage_mapping row yet,
    one is created automatically before anything else is saved.
    """
    try:
        result = await service.save_stage(request.to_dto(), current_user)
        return TemplateStageSaveResponse.from_dto(result)
    except BusinessRuleViolationError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e
