"""Unit Master — API controller. Thin: parse, delegate, respond."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.unit_schema import (
    UnitCreate,
    UnitListResponse,
    UnitResponse,
    UnitUpdate,
)
from src.application.dtos.masters.unit_dtos import CreateUnitDTO, UpdateUnitDTO
from src.application.services.masters.unit_service import UnitService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.unit_repository_impl import UnitRepositoryImpl
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/units", tags=["Masters - Unit"])

RESOURCE = "units"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> UnitService:
    return UnitService(repo=UnitRepositoryImpl(session))


@router.get(
    "",
    response_model=UnitListResponse,
    summary="List units",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_units(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    service: UnitService = Depends(_get_service),
) -> UnitListResponse:
    result = await service.list_units(skip=skip, limit=limit, search=search, is_active=is_active)
    return UnitListResponse(
        items=[UnitResponse(**item.__dict__) for item in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post(
    "",
    response_model=UnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a unit",
    dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))],
)
async def create_unit(
    request: UnitCreate,
    current_user: User = Depends(get_current_active_user),
    service: UnitService = Depends(_get_service),
) -> UnitResponse:
    try:
        result = await service.create_unit(
            dto=CreateUnitDTO(name=request.name, business_unit_id=request.business_unit_id, is_active=request.is_active),
            actor=current_user,
        )
        return UnitResponse(**result.__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get(
    "/{unit_id}",
    response_model=UnitResponse,
    summary="Get a unit by ID",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def get_unit(
    unit_id: int,
    service: UnitService = Depends(_get_service),
) -> UnitResponse:
    try:
        result = await service.get_unit(unit_id)
        return UnitResponse(**result.__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{unit_id}",
    response_model=UnitResponse,
    summary="Update a unit",
    dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))],
)
async def update_unit(
    unit_id: int,
    request: UnitUpdate,
    current_user: User = Depends(get_current_active_user),
    service: UnitService = Depends(_get_service),
) -> UnitResponse:
    try:
        result = await service.update_unit(
            unit_id=unit_id,
            dto=UpdateUnitDTO(name=request.name, business_unit_id=request.business_unit_id, is_active=request.is_active),
            actor=current_user,
        )
        return UnitResponse(**result.__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete(
    "/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a unit",
    dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))],
)
async def delete_unit(
    unit_id: int,
    service: UnitService = Depends(_get_service),
) -> None:
    try:
        await service.delete_unit(unit_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
