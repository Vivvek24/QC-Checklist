"""ChecklistStageSection — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.checklist_stage_section_schema import (
    ChecklistStageSectionCreate,
    ChecklistStageSectionListResponse,
    ChecklistStageSectionResponse,
    ChecklistStageSectionUpdate,
)
from src.application.dtos.qc_checklist.checklist_stage_section_dtos import (
    CreateChecklistStageSectionDTO,
    UpdateChecklistStageSectionDTO,
)
from src.application.services.qc_checklist.checklist_stage_section_service import ChecklistStageSectionService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.repositories.qc_checklist.checklist_stage_section_repository_impl import ChecklistStageSectionRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist/stage-sections", tags=["QC Checklist - Stage Sections"])
RESOURCE = "checklist_stage_sections"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> ChecklistStageSectionService:
    return ChecklistStageSectionService(repo=ChecklistStageSectionRepositoryImpl(session))


@router.get("", response_model=ChecklistStageSectionListResponse, summary="List checklist stage sections",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_sections(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    checklist_stage_id: int | None = Query(None),
    service: ChecklistStageSectionService = Depends(_get_service),
) -> ChecklistStageSectionListResponse:
    if checklist_stage_id is not None:
        items = await service.list_by_checklist_stage(checklist_stage_id)
        return ChecklistStageSectionListResponse(
            items=[ChecklistStageSectionResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    result = await service.list_sections(skip=skip, limit=limit)
    return ChecklistStageSectionListResponse(
        items=[ChecklistStageSectionResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=ChecklistStageSectionResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a checklist stage section",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_section(
    request: ChecklistStageSectionCreate,
    current_user: User = Depends(get_current_active_user),
    service: ChecklistStageSectionService = Depends(_get_service),
) -> ChecklistStageSectionResponse:
    dto = CreateChecklistStageSectionDTO(
        checklist_stage_id=request.checklist_stage_id,
        section_id=request.section_id,
    )
    return ChecklistStageSectionResponse(**(await service.create_section(dto, current_user)).__dict__)


@router.get("/{section_id}", response_model=ChecklistStageSectionResponse, summary="Get a checklist stage section",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_section(section_id: int, service: ChecklistStageSectionService = Depends(_get_service)) -> ChecklistStageSectionResponse:
    try:
        return ChecklistStageSectionResponse(**(await service.get_section(section_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{section_id}", response_model=ChecklistStageSectionResponse, summary="Update a checklist stage section",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_section(
    section_id: int, request: ChecklistStageSectionUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ChecklistStageSectionService = Depends(_get_service),
) -> ChecklistStageSectionResponse:
    try:
        dto = UpdateChecklistStageSectionDTO(
            checklist_stage_id=request.checklist_stage_id,
            section_id=request.section_id,
        )
        return ChecklistStageSectionResponse(**(await service.update_section(section_id, dto, current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a checklist stage section",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_section(section_id: int, service: ChecklistStageSectionService = Depends(_get_service)) -> None:
    try:
        await service.delete_section(section_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
