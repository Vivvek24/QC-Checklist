"""TestMaster — API controller."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_active_user
from src.api.v1.schemas.masters.test_master_schema import (
    TestMasterCreate,
    TestMasterListResponse,
    TestMasterResponse,
    TestMasterUpdate,
)
from src.application.dtos.masters.test_master_dtos import (
    CreateTestMasterDTO,
    UpdateTestMasterDTO,
)
from src.application.services.masters.test_master_service import TestMasterService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
)
from src.infrastructure.database.repositories.masters.test_master_repository_impl import (
    TestMasterRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/masters/test-masters", tags=["Masters - Test Master"])
RESOURCE = "test_masters"


def _get_service(session: AsyncSession = Depends(get_db_session)) -> TestMasterService:
    return TestMasterService(repo=TestMasterRepositoryImpl(session))


@router.get("", response_model=TestMasterListResponse, summary="List test masters",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def list_tests(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None), is_active: bool | None = Query(None),
    product_id: int | None = Query(None),
    service: TestMasterService = Depends(_get_service),
) -> TestMasterListResponse:
    if product_id is not None:
        items = await service.list_by_product(product_id)
        return TestMasterListResponse(
            items=[TestMasterResponse(**i.__dict__) for i in items],
            total=len(items), skip=0, limit=len(items),
        )
    result = await service.list_tests(skip=skip, limit=limit, search=search, is_active=is_active)
    return TestMasterListResponse(
        items=[TestMasterResponse(**i.__dict__) for i in result.items],
        total=result.total, skip=result.skip, limit=result.limit,
    )


@router.post("", response_model=TestMasterResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a test master",
             dependencies=[Depends(require_api_permission(RESOURCE, "CREATE"))])
async def create_test(
    request: TestMasterCreate,
    current_user: User = Depends(get_current_active_user),
    service: TestMasterService = Depends(_get_service),
) -> TestMasterResponse:
    try:
        dto = CreateTestMasterDTO(
            test_name=request.test_name,
            sample_description=request.sample_description,
            sample_qty=request.sample_qty,
            product_id=request.product_id,
            is_active=request.is_active,
        )
        return TestMasterResponse(**(await service.create_test(dto, current_user)).__dict__)
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{test_id}", response_model=TestMasterResponse, summary="Get a test master",
            dependencies=[Depends(require_api_permission(RESOURCE, "READ"))])
async def get_test(test_id: int, service: TestMasterService = Depends(_get_service)) -> TestMasterResponse:
    try:
        return TestMasterResponse(**(await service.get_test(test_id)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{test_id}", response_model=TestMasterResponse, summary="Update a test master",
              dependencies=[Depends(require_api_permission(RESOURCE, "UPDATE"))])
async def update_test(
    test_id: int, request: TestMasterUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TestMasterService = Depends(_get_service),
) -> TestMasterResponse:
    try:
        dto = UpdateTestMasterDTO(
            test_name=request.test_name,
            sample_description=request.sample_description,
            sample_qty=request.sample_qty,
            product_id=request.product_id,
            is_active=request.is_active,
        )
        return TestMasterResponse(**(await service.update_test(test_id, dto, current_user)).__dict__)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateEntityError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a test master",
               dependencies=[Depends(require_api_permission(RESOURCE, "DELETE"))])
async def delete_test(test_id: int, service: TestMasterService = Depends(_get_service)) -> None:
    try:
        await service.delete_test(test_id)
    except EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
