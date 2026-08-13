"""Stage Master — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.stage_schema import StageCreate, StageListResponse, StageResponse, StageUpdate
from src.application.dtos.masters.stage_dtos import CreateStageDTO, UpdateStageDTO
from src.application.services.masters.stage_service import StageService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.stage_repository_impl import StageRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/stages", tags=["Masters - Stage"])
RESOURCE = "stages"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> StageService:
    return StageService(repo=StageRepositoryImpl(session))


@router.get("", response_model=StageListResponse, summary="List stages",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_stages(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                      search: str | None = Query(None), is_active: bool | None = Query(None),
                      service: StageService = Depends(_get_service)) -> StageListResponse:
    result = await service.list_stages(skip=skip, limit=limit, search=search, is_active=is_active)
    return StageListResponse(items=[StageResponse(**i.__dict__) for i in result.items],
                             total=result.total, skip=result.skip, limit=result.limit)


@router.post("", response_model=StageResponse, status_code=status.HTTP_201_CREATED, summary="Create a stage",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_stage(request: StageCreate, current_user: User = Depends(get_current_active_user),
                       service: StageService = Depends(_get_service)) -> StageResponse:
    try:
        return StageResponse(**(await service.create_stage(CreateStageDTO(stage_name=request.stage_name, is_active=request.is_active), current_user)).__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{stage_id}", response_model=StageResponse, summary="Get a stage",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_stage(stage_id: int, service: StageService = Depends(_get_service)) -> StageResponse:
    try:
        return StageResponse(**(await service.get_stage(stage_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{stage_id}", response_model=StageResponse, summary="Update a stage",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_stage(stage_id: int, request: StageUpdate, current_user: User = Depends(get_current_active_user),
                       service: StageService = Depends(_get_service)) -> StageResponse:
    try:
        return StageResponse(**(await service.update_stage(stage_id, UpdateStageDTO(stage_name=request.stage_name, is_active=request.is_active), current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{stage_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a stage",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_stage(stage_id: int, service: StageService = Depends(_get_service)) -> None:
    try:
        await service.delete_stage(stage_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
