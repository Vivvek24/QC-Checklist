"""Section Master — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.section_schema import SectionCreate, SectionListResponse, SectionResponse, SectionUpdate
from src.application.dtos.masters.section_dtos import CreateSectionDTO, UpdateSectionDTO
from src.application.services.masters.section_service import SectionService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.section_repository_impl import SectionRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/sections", tags=["Masters - Section"])
RESOURCE = "sections"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> SectionService:
    return SectionService(repo=SectionRepositoryImpl(session))


@router.get("", response_model=SectionListResponse, summary="List sections",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_sections(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                        search: str | None = Query(None), is_active: bool | None = Query(None),
                        format_stage_mapping_id: int | None = Query(None),
                        service: SectionService = Depends(_get_service)) -> SectionListResponse:
    result = await service.list_sections(skip=skip, limit=limit, search=search, is_active=is_active, format_stage_mapping_id=format_stage_mapping_id)
    return SectionListResponse(items=[SectionResponse(**i.__dict__) for i in result.items],
                               total=result.total, skip=result.skip, limit=result.limit)


@router.post("", response_model=SectionResponse, status_code=status.HTTP_201_CREATED, summary="Create a section",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_section(request: SectionCreate, current_user: User = Depends(get_current_active_user),
                         service: SectionService = Depends(_get_service)) -> SectionResponse:
    try:
        return SectionResponse(**(await service.create_section(CreateSectionDTO(section_name=request.section_name, format_stage_mapping_id=request.format_stage_mapping_id, is_active=request.is_active), current_user)).__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{section_id}", response_model=SectionResponse, summary="Get a section",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_section(section_id: int, service: SectionService = Depends(_get_service)) -> SectionResponse:
    try:
        return SectionResponse(**(await service.get_section(section_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{section_id}", response_model=SectionResponse, summary="Update a section",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_section(section_id: int, request: SectionUpdate, current_user: User = Depends(get_current_active_user),
                         service: SectionService = Depends(_get_service)) -> SectionResponse:
    try:
        return SectionResponse(**(await service.update_section(section_id, UpdateSectionDTO(section_name=request.section_name, format_stage_mapping_id=request.format_stage_mapping_id, is_active=request.is_active), current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a section",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_section(section_id: int, service: SectionService = Depends(_get_service)) -> None:
    try:
        await service.delete_section(section_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
