"""ChecklistRequest — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.checklist_request_schema import (
    ChecklistRequestCreate,
    ChecklistRequestListResponse,
    ChecklistRequestResponse,
    ChecklistRequestUpdate,
)
from src.application.dtos.qc_checklist.checklist_request_dtos import CreateChecklistRequestDTO, UpdateChecklistRequestDTO
from src.application.services.qc_checklist.checklist_request_service import ChecklistRequestService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.qc_checklist.checklist_request_repository_impl import ChecklistRequestRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist/requests", tags=["QC Checklist - Requests"])
RESOURCE = "checklist_requests"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> ChecklistRequestService:
    return ChecklistRequestService(repo=ChecklistRequestRepositoryImpl(session))


@router.get("", response_model=ChecklistRequestListResponse, summary="List checklist requests",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_requests(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    service: ChecklistRequestService = Depends(_get_service),
) -> ChecklistRequestListResponse:
    result = await service.list_requests(skip=skip, limit=limit, search=search, is_active=is_active)
    return ChecklistRequestListResponse(
        items=[ChecklistRequestResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=ChecklistRequestResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a checklist request",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_request(
    request: ChecklistRequestCreate,
    current_user: User = Depends(get_current_active_user),
    service: ChecklistRequestService = Depends(_get_service),
) -> ChecklistRequestResponse:
    try:
        dto = CreateChecklistRequestDTO(
            request_number=request.request_number,
            status=request.status,
            status_format=request.status_format,
            is_last_stage=request.is_last_stage,
            is_removed=request.is_removed,
            approver_user_id=request.approver_user_id,
            format_id=request.format_id,
        )
        return ChecklistRequestResponse(**(await service.create_request(dto, current_user)).__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{request_id}", response_model=ChecklistRequestResponse, summary="Get a checklist request",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_request(request_id: int, service: ChecklistRequestService = Depends(_get_service)) -> ChecklistRequestResponse:
    try:
        return ChecklistRequestResponse(**(await service.get_request(request_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{request_id}", response_model=ChecklistRequestResponse, summary="Update a checklist request",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_request(
    request_id: int, request: ChecklistRequestUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ChecklistRequestService = Depends(_get_service),
) -> ChecklistRequestResponse:
    try:
        dto = UpdateChecklistRequestDTO(
            status=request.status,
            request_number=request.request_number,
            status_format=request.status_format,
            is_last_stage=request.is_last_stage,
            is_removed=request.is_removed,
            approver_user_id=request.approver_user_id,
            format_id=request.format_id,
        )
        return ChecklistRequestResponse(**(await service.update_request(request_id, dto, current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a checklist request",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_request(request_id: int, service: ChecklistRequestService = Depends(_get_service)) -> None:
    try:
        await service.delete_request(request_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
