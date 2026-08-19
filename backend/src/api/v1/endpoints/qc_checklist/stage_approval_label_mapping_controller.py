"""StageApprovalLabelMapping — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.qc_checklist.stage_approval_label_mapping_schema import (
    StageApprovalLabelMappingCreate,
    StageApprovalLabelMappingListResponse,
    StageApprovalLabelMappingResponse,
    StageApprovalLabelMappingUpdate,
)
from src.application.dtos.qc_checklist.stage_approval_label_mapping_dtos import (
    CreateStageApprovalLabelMappingDTO,
    UpdateStageApprovalLabelMappingDTO,
)
from src.application.services.qc_checklist.stage_approval_label_mapping_service import StageApprovalLabelMappingService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import EntityNotFoundError
from src.infrastructure.database.repositories.qc_checklist.stage_approval_label_mapping_repository_impl import StageApprovalLabelMappingRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/qc-checklist/stage-approval-label-mappings", tags=["QC Checklist - Stage Approval Label Mappings"])
RESOURCE = "stage_approval_label_mappings"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> StageApprovalLabelMappingService:
    return StageApprovalLabelMappingService(repo=StageApprovalLabelMappingRepositoryImpl(session))


@router.get("", response_model=StageApprovalLabelMappingListResponse, summary="List stage approval label mappings",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_mappings(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    checklist_stage_id: int | None = Query(None),
    approval_label_id: int | None = Query(None),
    service: StageApprovalLabelMappingService = Depends(_get_service),
) -> StageApprovalLabelMappingListResponse:
    if checklist_stage_id is not None:
        items = await service.list_by_checklist_stage(checklist_stage_id)
        return StageApprovalLabelMappingListResponse(
            items=[StageApprovalLabelMappingResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    if approval_label_id is not None:
        items = await service.list_by_approval_label(approval_label_id)
        return StageApprovalLabelMappingListResponse(
            items=[StageApprovalLabelMappingResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    result = await service.list_mappings(skip=skip, limit=limit)
    return StageApprovalLabelMappingListResponse(
        items=[StageApprovalLabelMappingResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=StageApprovalLabelMappingResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a stage approval label mapping",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_mapping(
    request: StageApprovalLabelMappingCreate,
    current_user: User = Depends(get_current_active_user),
    service: StageApprovalLabelMappingService = Depends(_get_service),
) -> StageApprovalLabelMappingResponse:
    dto = CreateStageApprovalLabelMappingDTO(
        checklist_stage_id=request.checklist_stage_id,
        approval_label_id=request.approval_label_id,
        remark_id=request.remark_id,
        user_id=request.user_id,
        role_id=request.role_id,
        date_of_action=request.date_of_action,
        remark=request.remark,
        is_show=request.is_show,
        is_refer_back=request.is_refer_back,
    )
    return StageApprovalLabelMappingResponse(**(await service.create_mapping(dto, current_user)).__dict__)


@router.get("/{mapping_id}", response_model=StageApprovalLabelMappingResponse, summary="Get a stage approval label mapping",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_mapping(mapping_id: int, service: StageApprovalLabelMappingService = Depends(_get_service)) -> StageApprovalLabelMappingResponse:
    try:
        return StageApprovalLabelMappingResponse(**(await service.get_mapping(mapping_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{mapping_id}", response_model=StageApprovalLabelMappingResponse, summary="Update a stage approval label mapping",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_mapping(
    mapping_id: int, request: StageApprovalLabelMappingUpdate,
    current_user: User = Depends(get_current_active_user),
    service: StageApprovalLabelMappingService = Depends(_get_service),
) -> StageApprovalLabelMappingResponse:
    try:
        dto = UpdateStageApprovalLabelMappingDTO(
            approval_label_id=request.approval_label_id,
            remark_id=request.remark_id,
            user_id=request.user_id,
            role_id=request.role_id,
            date_of_action=request.date_of_action,
            remark=request.remark,
            is_show=request.is_show,
            is_refer_back=request.is_refer_back,
        )
        return StageApprovalLabelMappingResponse(**(await service.update_mapping(mapping_id, dto, current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a stage approval label mapping",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_mapping(mapping_id: int, service: StageApprovalLabelMappingService = Depends(_get_service)) -> None:
    try:
        await service.delete_mapping(mapping_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
