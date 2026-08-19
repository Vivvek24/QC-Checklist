"""ChecklistStage — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.checklist_stage_schema import (
    ChecklistStageCreate,
    ChecklistStageListResponse,
    ChecklistStageResponse,
    ChecklistStageUpdate,
)
from src.application.dtos.qc_checklist.checklist_stage_dtos import CreateChecklistStageDTO, UpdateChecklistStageDTO
from src.application.services.qc_checklist.checklist_stage_service import ChecklistStageService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.repositories.qc_checklist.checklist_stage_repository_impl import ChecklistStageRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist/stages", tags=["QC Checklist - Stages"])
RESOURCE = "checklist_stages"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> ChecklistStageService:
    return ChecklistStageService(repo=ChecklistStageRepositoryImpl(session))


@router.get("", response_model=ChecklistStageListResponse, summary="List checklist stages",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_stages(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None),
    checklist_request_id: int | None = Query(None),
    service: ChecklistStageService = Depends(_get_service),
) -> ChecklistStageListResponse:
    if checklist_request_id is not None:
        items = await service.list_by_checklist_request(checklist_request_id)
        return ChecklistStageListResponse(
            items=[ChecklistStageResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    result = await service.list_stages(skip=skip, limit=limit, search=search)
    return ChecklistStageListResponse(
        items=[ChecklistStageResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=ChecklistStageResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a checklist stage",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_stage(
    request: ChecklistStageCreate,
    current_user: User = Depends(get_current_active_user),
    service: ChecklistStageService = Depends(_get_service),
) -> ChecklistStageResponse:
    dto = CreateChecklistStageDTO(
        checklist_request_id=request.checklist_request_id,
        user_id=request.user_id,
        format_stage_mapping_id=request.format_stage_mapping_id,
        status=request.status,
        performed_remark=request.performed_remark,
        approved_remark=request.approved_remark,
        is_self_verified=request.is_self_verified,
        self_verification_details=request.self_verification_details,
        is_approvable=request.is_approvable,
        is_last_stage=request.is_last_stage,
        submit_remarks=request.submit_remarks,
        self_approved_remark=request.self_approved_remark,
    )
    return ChecklistStageResponse(**(await service.create_stage(dto, current_user)).__dict__)


@router.get("/{stage_id}", response_model=ChecklistStageResponse, summary="Get a checklist stage",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_stage(stage_id: int, service: ChecklistStageService = Depends(_get_service)) -> ChecklistStageResponse:
    try:
        return ChecklistStageResponse(**(await service.get_stage(stage_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{stage_id}", response_model=ChecklistStageResponse, summary="Update a checklist stage",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_stage(
    stage_id: int, request: ChecklistStageUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ChecklistStageService = Depends(_get_service),
) -> ChecklistStageResponse:
    try:
        dto = UpdateChecklistStageDTO(
            status=request.status,
            user_id=request.user_id,
            format_stage_mapping_id=request.format_stage_mapping_id,
            performed_remark=request.performed_remark,
            approved_remark=request.approved_remark,
            is_self_verified=request.is_self_verified,
            self_verification_details=request.self_verification_details,
            is_approvable=request.is_approvable,
            is_last_stage=request.is_last_stage,
            submit_remarks=request.submit_remarks,
            self_approved_remark=request.self_approved_remark,
        )
        return ChecklistStageResponse(**(await service.update_stage(stage_id, dto, current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{stage_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a checklist stage",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_stage(stage_id: int, service: ChecklistStageService = Depends(_get_service)) -> None:
    try:
        await service.delete_stage(stage_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
