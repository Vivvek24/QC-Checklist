"""
Business Unit Master — API controller.
Thin: parses HTTP, delegates to BusinessUnitService, maps errors to HTTP codes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.business_unit_schema import (
    BusinessUnitCreate,
    BusinessUnitListResponse,
    BusinessUnitResponse,
    BusinessUnitUpdate,
)
from src.application.dtos.masters.business_unit_dtos import (
    CreateBusinessUnitDTO,
    UpdateBusinessUnitDTO,
)
from src.application.services.masters.business_unit_service import BusinessUnitService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.infrastructure.database.repositories.masters.business_unit_repository_impl import (
    BusinessUnitRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/business-units", tags=["Masters - Business Unit"])

RESOURCE = "business_units"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> BusinessUnitService:
    """Build BusinessUnitService with injected repository."""
    return BusinessUnitService(repo=BusinessUnitRepositoryImpl(session))


@router.get(
    "",
    response_model=BusinessUnitListResponse,
    summary="List business units",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def list_business_units(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    search: str | None = Query(default=None, description="Filter by name"),
    is_active: bool | None = Query(default=None),
    service: BusinessUnitService = Depends(_get_service),
) -> BusinessUnitListResponse:
    """GET /api/v1/masters/business-units"""
    result = await service.list_business_units(
        skip=skip, limit=limit, search=search, is_active=is_active
    )
    return BusinessUnitListResponse(
        items=[BusinessUnitResponse(**item.__dict__) for item in result.items],
        total=result.total,
        skip=result.skip,
        limit=result.limit,
    )


@router.post(
    "",
    response_model=BusinessUnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a business unit",
    dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))],
)
async def create_business_unit(
    request: BusinessUnitCreate,
    current_user: User = Depends(get_current_active_user),
    service: BusinessUnitService = Depends(_get_service),
) -> BusinessUnitResponse:
    """POST /api/v1/masters/business-units"""
    try:
        result = await service.create_business_unit(
            dto=CreateBusinessUnitDTO(name=request.name, is_active=request.is_active),
            actor=current_user,
        )
        return BusinessUnitResponse(**result.__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get(
    "/{business_unit_id}",
    response_model=BusinessUnitResponse,
    summary="Get a business unit by ID",
    dependencies=[Depends(require_api_permission(RESOURCE, "READ"))],
)
async def get_business_unit(
    business_unit_id: int,
    service: BusinessUnitService = Depends(_get_service),
) -> BusinessUnitResponse:
    """GET /api/v1/masters/business-units/{business_unit_id}"""
    try:
        result = await service.get_business_unit(business_unit_id)
        return BusinessUnitResponse(**result.__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{business_unit_id}",
    response_model=BusinessUnitResponse,
    summary="Update a business unit",
    dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))],
)
async def update_business_unit(
    business_unit_id: int,
    request: BusinessUnitUpdate,
    current_user: User = Depends(get_current_active_user),
    service: BusinessUnitService = Depends(_get_service),
) -> BusinessUnitResponse:
    """PATCH /api/v1/masters/business-units/{business_unit_id}"""
    try:
        result = await service.update_business_unit(
            business_unit_id=business_unit_id,
            dto=UpdateBusinessUnitDTO(name=request.name, is_active=request.is_active),
            actor=current_user,
        )
        return BusinessUnitResponse(**result.__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete(
    "/{business_unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a business unit",
    dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))],
)
async def delete_business_unit(
    business_unit_id: int,
    service: BusinessUnitService = Depends(_get_service),
) -> None:
    """DELETE /api/v1/masters/business-units/{business_unit_id}"""
    try:
        await service.delete_business_unit(business_unit_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
