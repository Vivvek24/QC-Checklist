"""StageQuestionMapping — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.stage_question_mapping_schema import (
    StageQuestionMappingCreate,
    StageQuestionMappingListResponse,
    StageQuestionMappingResponse,
    StageQuestionMappingUpdate,
)
from src.application.dtos.masters.stage_question_mapping_dtos import (
    CreateStageQuestionMappingDTO,
    UpdateStageQuestionMappingDTO,
)
from src.application.services.masters.stage_question_mapping_service import (
    StageQuestionMappingService,
)
from src.domain.entities.user import User
from src.domain.enums.custom_answer_enum import CustomAnswer
from src.domain.exceptions.domain_exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
)
from src.infrastructure.database.repositories.masters.stage_question_mapping_repository_impl import (
    StageQuestionMappingRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(
    prefix="/masters/stage-question-mappings",
    tags=["Masters - Stage Question Mapping"],
)
RESOURCE = "stage_question_mappings"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> StageQuestionMappingService:
    return StageQuestionMappingService(repo=StageQuestionMappingRepositoryImpl(session))


def _to_custom_answer(val) -> CustomAnswer | None:
    if val is None:
        return None
    return CustomAnswer(val.value) if val else None


@router.get("", response_model=StageQuestionMappingListResponse, summary="List stage-question mappings",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_mappings(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    is_active: bool | None = Query(None),
    format_stage_mapping_id: int | None = Query(None),
    service: StageQuestionMappingService = Depends(_get_service),
) -> StageQuestionMappingListResponse:
    if format_stage_mapping_id is not None:
        items = await service.list_by_format_stage_mapping(format_stage_mapping_id)
        return StageQuestionMappingListResponse(
            items=[StageQuestionMappingResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    result = await service.list_mappings(skip=skip, limit=limit, is_active=is_active)
    return StageQuestionMappingListResponse(
        items=[StageQuestionMappingResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=StageQuestionMappingResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a stage-question mapping",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_mapping(
    request: StageQuestionMappingCreate,
    current_user: User = Depends(get_current_active_user),
    service: StageQuestionMappingService = Depends(_get_service),
) -> StageQuestionMappingResponse:
    try:
        dto = CreateStageQuestionMappingDTO(
            format_stage_mapping_id=request.format_stage_mapping_id,
            question_id=request.question_id,
            sap_field_id=request.sap_field_id,
            section_id=request.section_id,
            serial_number=request.serial_number,
            show_on_grid=request.show_on_grid,
            aql_limit=request.aql_limit,
            is_declaration_question=request.is_declaration_question,
            is_editable=request.is_editable,
            custom_answers=_to_custom_answer(request.custom_answers),
            is_active=request.is_active,
        )
        result = await service.create_mapping(dto, current_user)
        return StageQuestionMappingResponse(**result.__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{mapping_id}", response_model=StageQuestionMappingResponse,
            summary="Get a stage-question mapping",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_mapping(
    mapping_id: int, service: StageQuestionMappingService = Depends(_get_service)
) -> StageQuestionMappingResponse:
    try:
        return StageQuestionMappingResponse(**(await service.get_mapping(mapping_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{mapping_id}", response_model=StageQuestionMappingResponse,
              summary="Update a stage-question mapping",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_mapping(
    mapping_id: int, request: StageQuestionMappingUpdate,
    current_user: User = Depends(get_current_active_user),
    service: StageQuestionMappingService = Depends(_get_service),
) -> StageQuestionMappingResponse:
    try:
        dto = UpdateStageQuestionMappingDTO(
            format_stage_mapping_id=request.format_stage_mapping_id,
            question_id=request.question_id,
            sap_field_id=request.sap_field_id,
            section_id=request.section_id,
            serial_number=request.serial_number,
            show_on_grid=request.show_on_grid,
            aql_limit=request.aql_limit,
            is_declaration_question=request.is_declaration_question,
            is_editable=request.is_editable,
            custom_answers=_to_custom_answer(request.custom_answers),
            is_active=request.is_active,
        )
        result = await service.update_mapping(mapping_id, dto, current_user)
        return StageQuestionMappingResponse(**result.__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a stage-question mapping",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_mapping(
    mapping_id: int, service: StageQuestionMappingService = Depends(_get_service)
) -> None:
    try:
        await service.delete_mapping(mapping_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
