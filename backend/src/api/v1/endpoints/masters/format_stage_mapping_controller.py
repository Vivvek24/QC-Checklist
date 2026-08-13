"""FormatStageMapping — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.format_stage_mapping_schema import (
    FormatStageMappingCreate,
    FormatStageMappingListResponse,
    FormatStageMappingResponse,
    FormatStageMappingUpdate,
)
from src.application.dtos.masters.format_stage_mapping_dtos import CreateFormatStageMappingDTO, UpdateFormatStageMappingDTO
from src.application.services.masters.format_stage_mapping_service import FormatStageMappingService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.format_stage_mapping_repository_impl import FormatStageMappingRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/format-stage-mappings", tags=["Masters - Format Stage Mapping"])
RESOURCE = "format_stage_mappings"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> FormatStageMappingService:
    return FormatStageMappingService(repo=FormatStageMappingRepositoryImpl(session))


@router.get("", response_model=FormatStageMappingListResponse, summary="List format-stage mappings",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_mappings(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    is_active: bool | None = Query(None),
    format_id: int | None = Query(None),
    stage_id: int | None = Query(None),
    service: FormatStageMappingService = Depends(_get_service),
) -> FormatStageMappingListResponse:
    if format_id is not None:
        items = await service.list_by_format(format_id)
        return FormatStageMappingListResponse(
            items=[FormatStageMappingResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    if stage_id is not None:
        items = await service.list_by_stage(stage_id)
        return FormatStageMappingListResponse(
            items=[FormatStageMappingResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    result = await service.list_mappings(skip=skip, limit=limit, is_active=is_active)
    return FormatStageMappingListResponse(
        items=[FormatStageMappingResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=FormatStageMappingResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a format-stage mapping",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_mapping(
    request: FormatStageMappingCreate,
    current_user: User = Depends(get_current_active_user),
    service: FormatStageMappingService = Depends(_get_service),
) -> FormatStageMappingResponse:
    try:
        dto = CreateFormatStageMappingDTO(
            format_id=request.format_id,
            stage_id=request.stage_id,
            is_active=request.is_active,
            is_approvable=request.is_approvable,
            is_refer_back=request.is_refer_back,
            has_section=request.has_section,
        )
        return FormatStageMappingResponse(**(await service.create_mapping(dto, current_user)).__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{mapping_id}", response_model=FormatStageMappingResponse, summary="Get a format-stage mapping",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_mapping(mapping_id: int, service: FormatStageMappingService = Depends(_get_service)) -> FormatStageMappingResponse:
    try:
        return FormatStageMappingResponse(**(await service.get_mapping(mapping_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{mapping_id}", response_model=FormatStageMappingResponse, summary="Update a format-stage mapping",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_mapping(
    mapping_id: int, request: FormatStageMappingUpdate,
    current_user: User = Depends(get_current_active_user),
    service: FormatStageMappingService = Depends(_get_service),
) -> FormatStageMappingResponse:
    try:
        dto = UpdateFormatStageMappingDTO(
            format_id=request.format_id,
            stage_id=request.stage_id,
            is_active=request.is_active,
            is_approvable=request.is_approvable,
            is_refer_back=request.is_refer_back,
            has_section=request.has_section,
        )
        return FormatStageMappingResponse(**(await service.update_mapping(mapping_id, dto, current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a format-stage mapping",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_mapping(mapping_id: int, service: FormatStageMappingService = Depends(_get_service)) -> None:
    try:
        await service.delete_mapping(mapping_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
