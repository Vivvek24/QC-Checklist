"""
LDAP Service API endpoints.
Thin controller — delegates all logic to LdapService.

Management (grid CRUD):
  - GET    /services/ldap/configs               — List configured LDAP servers
  - POST   /services/ldap/configs               — Create a configuration
  - GET    /services/ldap/configs/{id}          — Get a configuration
  - PUT    /services/ldap/configs/{id}          — Update a configuration
  - DELETE /services/ldap/configs/{id}          — Delete a configuration

Services (per-server operations):
  - GET  /services/ldap/configs/{id}/health               — Check reachability
  - POST /services/ldap/configs/{id}/validate-credentials — Validate a user

Protected: requires the 'services.ldap' permission.
"""

from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import (
    get_current_active_user,
    get_ldap_config_repository,
)
from src.api.v1.schemas.ldap_schema import (
    LdapConfigCreateRequest,
    LdapConfigListResponse,
    LdapConfigResponse,
    LdapConfigUpdateRequest,
    LdapHealthResponse,
    ValidateLdapCredentialsRequest,
    ValidateLdapCredentialsResponse,
)
from src.application.services.ldap_service import LdapService
from src.domain.entities.user import User
from src.domain.repositories.ldap_config_repository import ILdapConfigRepository
from src.infrastructure.external.ldap.ldap_client import (
    LdapAuthError,
    LdapError,
    LdapUnavailableError,
)
from src.infrastructure.security.permission_manager import require_permission

router = APIRouter(
    prefix="/services/ldap",
    tags=["LDAP Service"],
    dependencies=[Depends(require_permission("services.ldap"))],
)


def _get_ldap_service(
    repository: ILdapConfigRepository = Depends(get_ldap_config_repository),
) -> LdapService:
    """FastAPI dependency — creates LdapService with injected dependencies."""
    return LdapService(repository=repository)


def _raise_for_ldap_error(exc: LdapError) -> NoReturn:
    """
    Map LDAP client/service exceptions to HTTP responses.

    Declared `NoReturn`, not `None`: every branch raises. With `None`, mypy treats
    a caller's `except LdapError: _raise_for_ldap_error(exc)` as falling off the
    end of the function and reports a missing return — which hides the fact that a
    genuine fall-through would look identical.
    """
    if isinstance(exc, LdapAuthError):
        raise HTTPException(status_code=401, detail=exc.detail) from exc
    if isinstance(exc, LdapUnavailableError):
        raise HTTPException(status_code=503, detail=exc.detail) from exc
    raise HTTPException(status_code=502, detail=exc.detail) from exc


# ─── Management: CRUD ───


@router.get(
    "/configs",
    response_model=LdapConfigListResponse,
    summary="List configured LDAP servers",
)
async def list_configs(
    service: LdapService = Depends(_get_ldap_service),
) -> LdapConfigListResponse:
    """List all LDAP server configurations (bind passwords are never returned)."""
    return await service.list_configs()


@router.post(
    "/configs",
    response_model=LdapConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an LDAP server configuration",
)
async def create_config(
    request: LdapConfigCreateRequest,
    current_user: User = Depends(get_current_active_user),
    service: LdapService = Depends(_get_ldap_service),
) -> LdapConfigResponse:
    """Create a new LDAP server configuration."""
    return await service.create_config(actor=current_user, request=request)


@router.get(
    "/configs/{config_id}",
    response_model=LdapConfigResponse,
    summary="Get an LDAP server configuration",
)
async def get_config(
    config_id: UUID,
    service: LdapService = Depends(_get_ldap_service),
) -> LdapConfigResponse:
    """Get a single LDAP server configuration by id."""
    return await service.get_config(config_id)


@router.put(
    "/configs/{config_id}",
    response_model=LdapConfigResponse,
    summary="Update an LDAP server configuration",
)
async def update_config(
    config_id: UUID,
    request: LdapConfigUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    service: LdapService = Depends(_get_ldap_service),
) -> LdapConfigResponse:
    """Update an LDAP server configuration. Omit the password to keep the current one."""
    return await service.update_config(
        actor=current_user, config_id=config_id, request=request
    )


@router.delete(
    "/configs/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an LDAP server configuration",
)
async def delete_config(
    config_id: UUID,
    service: LdapService = Depends(_get_ldap_service),
) -> None:
    """Delete an LDAP server configuration."""
    await service.delete_config(config_id)


# ─── Services: health + validation ───


@router.get(
    "/configs/{config_id}/health",
    response_model=LdapHealthResponse,
    summary="Check LDAP server reachability",
)
async def check_health(
    config_id: UUID,
    service: LdapService = Depends(_get_ldap_service),
) -> LdapHealthResponse:
    """Verify whether the given LDAP server is reachable and can be bound."""
    return await service.check_health(config_id)


@router.post(
    "/configs/{config_id}/validate-credentials",
    response_model=ValidateLdapCredentialsResponse,
    summary="Validate a user's credentials via LDAP",
)
async def validate_credentials(
    config_id: UUID,
    request: ValidateLdapCredentialsRequest,
    service: LdapService = Depends(_get_ldap_service),
) -> ValidateLdapCredentialsResponse:
    """Validate a username/password pair by attempting an LDAP bind."""
    try:
        return await service.validate_credentials(
            config_id=config_id,
            username=request.username,
            password=request.password,
        )
    except LdapError as exc:
        _raise_for_ldap_error(exc)
