"""Format Master — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.format_schema import (
    FormatCreate, FormatListResponse, FormatResponse, FormatUpdate,
)
from src.application.dtos.masters.format_dtos import CreateFormatDTO, UpdateFormatDTO
from src.application.services.masters.format_service import FormatService
from src.domain.entities.user import User
from src.domain.enums.format_enums import FormatType
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.format_repository_impl import FormatRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/formats", tags=["Masters - Format"])

RESOURCE = "formats"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> FormatService:
    return FormatService(repo=FormatRepositoryImpl(session))


@router.get("", response_model=FormatListResponse, summary="List formats",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_formats(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    service: FormatService = Depends(_get_service),
) -> FormatListResponse:
    result = await service.list_formats(skip=skip, limit=limit, search=search, is_active=is_active)
    return FormatListResponse(
        items=[FormatResponse(**item.__dict__) for item in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=FormatResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a format", dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_format(
    request: FormatCreate,
    current_user: User = Depends(get_current_active_user),
    service: FormatService = Depends(_get_service),
) -> FormatResponse:
    try:
        result = await service.create_format(
            dto=CreateFormatDTO(
                format_no=request.format_no, format_title=request.format_title,
                format_name=request.format_name, unit_id=request.unit_id,
                format_type=request.format_type, has_declaration_question=request.has_declaration_question,
                is_active=request.is_active,
            ),
            actor=current_user,
        )
        return FormatResponse(**result.__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{format_id}", response_model=FormatResponse, summary="Get a format",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_format(format_id: int, service: FormatService = Depends(_get_service)) -> FormatResponse:
    try:
        return FormatResponse(**(await service.get_format(format_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{format_id}", response_model=FormatResponse, summary="Update a format",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_format(
    format_id: int,
    request: FormatUpdate,
    current_user: User = Depends(get_current_active_user),
    service: FormatService = Depends(_get_service),
) -> FormatResponse:
    try:
        result = await service.update_format(
            format_id=format_id,
            dto=UpdateFormatDTO(
                format_no=request.format_no, format_title=request.format_title,
                format_name=request.format_name, unit_id=request.unit_id,
                format_type=request.format_type, has_declaration_question=request.has_declaration_question,
                is_active=request.is_active,
            ),
            actor=current_user,
        )
        return FormatResponse(**result.__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{format_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a format",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_format(format_id: int, service: FormatService = Depends(_get_service)) -> None:
    try:
        await service.delete_format(format_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
