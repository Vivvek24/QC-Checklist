"""Template — API controller (thin).

Parses HTTP, delegates to the service, and maps domain errors to HTTP status
codes. No business rules or ORM access here.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.template_schema import (
    ReplaceColumnsForScopeRequest,
    TemplateColumnListResponse,
    TemplateColumnResponse,
    TemplateResponse,
)
from src.application.dtos.masters.template_dtos import (
    ColumnInputDTO,
    ReplaceColumnsForScopeDTO,
    TemplateDTO,
    TemplateLayoutColumnDTO,
)
from src.application.services.masters.template_service import TemplateService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import BusinessRuleViolationError
from src.infrastructure.database.repositories.masters.template_layout_column_repository_impl import (  # noqa: E501
    TemplateLayoutColumnRepositoryImpl,
)
from src.infrastructure.database.repositories.masters.template_repository_impl import (
    TemplateRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/templates", tags=["Template"])
RESOURCE = "templates"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> TemplateService:
    return TemplateService(
        template_repo=TemplateRepositoryImpl(session),
        column_repo=TemplateLayoutColumnRepositoryImpl(session),
    )


def _template_to_response(dto: TemplateDTO) -> TemplateResponse:
    return TemplateResponse(
        id=dto.id,
        format_id=dto.format_id,
        is_active=dto.is_active,
        created_by=dto.created_by,
        created_date=dto.created_date,
        modified_by=dto.modified_by,
        modified_date=dto.modified_date,
    )


def _column_to_response(dto: TemplateLayoutColumnDTO) -> TemplateColumnResponse:
    return TemplateColumnResponse(
        id=dto.id,
        template_id=dto.template_id,
        format_stage_mapping_id=dto.format_stage_mapping_id,
        section_id=dto.section_id,
        header=dto.header,
        column_type=dto.column_type,
        display_order=dto.display_order,
        width=dto.width,
        is_required=dto.is_required,
    )


def _to_replace_columns_dto(request: ReplaceColumnsForScopeRequest) -> ReplaceColumnsForScopeDTO:
    return ReplaceColumnsForScopeDTO(
        format_id=request.format_id,
        format_stage_mapping_id=request.format_stage_mapping_id,
        section_id=request.section_id,
        columns=[
            ColumnInputDTO(
                header=c.header,
                column_type=c.column_type,
                display_order=index,
                width=c.width,
                is_required=c.is_required,
            )
            for index, c in enumerate(request.columns)
        ],
    )


@router.get(
    "/by-format/{format_id}",
    response_model=TemplateResponse,
    summary="Get or create the template for a format",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def get_or_create_template_for_format(
    format_id: int,
    current_user: User = Depends(get_current_active_user),
    service: TemplateService = Depends(_get_service),
) -> TemplateResponse:
    dto = await service.get_or_create_for_format(format_id, current_user)
    return _template_to_response(dto)


@router.get(
    "/columns",
    response_model=TemplateColumnListResponse,
    summary="List columns for a stage/section scope",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_columns_for_scope(
    format_stage_mapping_id: int = Query(..., ge=1),
    section_id: int | None = Query(None),
    service: TemplateService = Depends(_get_service),
) -> TemplateColumnListResponse:
    items = await service.list_columns_for_scope(format_stage_mapping_id, section_id)
    return TemplateColumnListResponse(items=[_column_to_response(i) for i in items])


@router.get(
    "/columns/by-stage",
    response_model=TemplateColumnListResponse,
    summary="List all columns (stage-level and every section) under one stage mapping",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_columns_for_stage(
    format_stage_mapping_id: int = Query(..., ge=1),
    service: TemplateService = Depends(_get_service),
) -> TemplateColumnListResponse:
    items = await service.list_columns_for_stage(format_stage_mapping_id)
    return TemplateColumnListResponse(items=[_column_to_response(i) for i in items])


@router.put(
    "/columns",
    response_model=TemplateColumnListResponse,
    summary="Replace all columns for a stage/section scope",
    dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))],
)
async def replace_columns_for_scope(
    request: ReplaceColumnsForScopeRequest,
    current_user: User = Depends(get_current_active_user),
    service: TemplateService = Depends(_get_service),
) -> TemplateColumnListResponse:
    try:
        items = await service.replace_columns_for_scope(
            _to_replace_columns_dto(request), current_user
        )
        return TemplateColumnListResponse(items=[_column_to_response(i) for i in items])
    except BusinessRuleViolationError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.delete(
    "/columns",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete all columns for a stage/section scope",
    dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))],
)
async def delete_columns_for_scope(
    format_stage_mapping_id: int = Query(..., ge=1),
    section_id: int | None = Query(None),
    service: TemplateService = Depends(_get_service),
) -> None:
    await service.delete_columns_for_scope(format_stage_mapping_id, section_id)
