"""
Darwinbox Service API endpoints.
Thin controller — delegates all business logic to DarwinboxService.

Endpoints:
  - GET  /health     — Check Darwinbox service reachability
  - GET  /employees  — Fetch the raw employee master from Darwinbox (no persistence)
  - GET  /stored     — List employees already synced into the local database
  - POST /sync       — Fetch from Darwinbox and upsert into the local database

Protected: requires the 'services.darwinbox' permission.
"""

from typing import Any, Literal, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.v1.dependencies import (
    get_current_active_user,
    get_darwinbox_employee_repository,
)
from src.api.v1.schemas.darwinbox_schema import (
    DarwinboxEmployeeListResponse,
    DarwinboxHealthResponse,
    SyncEmployeesResponse,
)
from src.application.services.darwinbox_service import DarwinboxService
from src.domain.entities.user import User
from src.domain.repositories.darwinbox_employee_repository import (
    IDarwinboxEmployeeRepository,
)
from src.infrastructure.external.darwinbox.darwinbox_client import (
    DarwinboxAuthError,
    DarwinboxClient,
    DarwinboxError,
    DarwinboxUnavailableError,
)
from src.infrastructure.security.permission_manager import require_permission

router = APIRouter(
    prefix="/services/darwinbox",
    tags=["Darwinbox Service"],
    dependencies=[Depends(require_permission("services.darwinbox"))],
)


def _get_darwinbox_service(
    repository: IDarwinboxEmployeeRepository = Depends(
        get_darwinbox_employee_repository
    ),
) -> DarwinboxService:
    """FastAPI dependency — creates DarwinboxService with injected dependencies."""
    return DarwinboxService(client=DarwinboxClient(), repository=repository)


def _resolve_datasets(
    scope: Literal["active", "inactive", "all"],
) -> list[Literal["active", "inactive"]]:
    """Expand a sync scope into the concrete list of datasets to fetch."""
    if scope == "all":
        return ["active", "inactive"]
    return [scope]


def _raise_for_darwinbox_error(exc: DarwinboxError) -> NoReturn:
    """
    Map Darwinbox client/service exceptions to HTTP responses.

    Declared `NoReturn`, not `None`: every branch raises. With `None`, mypy treats
    a caller's `except DarwinboxError: _raise_for_darwinbox_error(exc)` as falling
    off the end of the function and reports a missing return on every endpoint —
    which hides the fact that a genuine fall-through would look identical.
    """
    if isinstance(exc, DarwinboxAuthError):
        raise HTTPException(status_code=401, detail=exc.detail) from exc
    if isinstance(exc, DarwinboxUnavailableError):
        raise HTTPException(status_code=503, detail=exc.detail) from exc
    raise HTTPException(status_code=502, detail=exc.detail) from exc


@router.get(
    "/health",
    response_model=DarwinboxHealthResponse,
    summary="Check Darwinbox service reachability",
)
async def check_health(
    service: DarwinboxService = Depends(_get_darwinbox_service),
) -> DarwinboxHealthResponse:
    """Verify whether the Darwinbox service is reachable."""
    return await service.check_health()


@router.get("/employees", summary="Fetch raw employee master from Darwinbox")
async def get_employees(
    dataset: Literal["active", "inactive"] = Query(
        default="active", description="Which Darwinbox dataset to fetch"
    ),
    service: DarwinboxService = Depends(_get_darwinbox_service),
) -> dict[str, Any]:
    """Fetch the employee master for a dataset from Darwinbox without persisting."""
    try:
        return await service.fetch_remote_employees(dataset)
    except DarwinboxError as exc:
        _raise_for_darwinbox_error(exc)


@router.get(
    "/stored",
    response_model=DarwinboxEmployeeListResponse,
    summary="List employees stored in the local database",
)
async def list_stored_employees(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    status: str | None = Query(
        default=None, description="Filter by employee_status, e.g. 'Active'"
    ),
    search: str | None = Query(
        default=None, description="Search by employee id, name, email or department"
    ),
    service: DarwinboxService = Depends(_get_darwinbox_service),
) -> DarwinboxEmployeeListResponse:
    """List Darwinbox employees already synced into the local database."""
    return await service.list_employees(
        skip=skip, limit=limit, status=status, search=search
    )


@router.post(
    "/sync",
    response_model=SyncEmployeesResponse,
    summary="Sync employee master from Darwinbox into the database",
)
async def sync_employees(
    scope: Literal["active", "inactive", "all"] = Query(
        default="all",
        description="Which population to sync: active, inactive, or all",
    ),
    current_user: User = Depends(get_current_active_user),
    service: DarwinboxService = Depends(_get_darwinbox_service),
) -> SyncEmployeesResponse:
    """Fetch the selected Darwinbox dataset(s) and upsert into the database."""
    try:
        return await service.sync_employees(
            actor=current_user, datasets=_resolve_datasets(scope)
        )
    except DarwinboxError as exc:
        _raise_for_darwinbox_error(exc)
