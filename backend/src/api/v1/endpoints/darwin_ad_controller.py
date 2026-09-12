"""
Published Darwin AD service endpoints.

Migration target for the legacy Mendix "Darwin AD integrator" service. These
endpoints reproduce the original paths and request/response contracts so that
consuming applications only need to change the base URL (host), not their code.

Endpoints (matching the Mendix contract):
  - GET  /getemployees        — All employees
  - POST /getselectedemployees — Employees by a comma-separated list of ids/emails
  - POST /getemployeedetails   — Employee details by a comma-separated list of ids/emails
  - POST /validatecredentials  — HELD: requires LDAP, implemented separately (501)

Data source: the locally-synced ``darwinbox_employees`` table (no live AD/LDAP
dependency for the read endpoints).

Auth: optional shared secret via the ``X-API-Key`` header, enforced only when
``settings.DARWIN_PUBLISHED_API_KEY`` is configured.
"""

import secrets

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query, status

from src.api.v1.dependencies import (
    get_credential_cipher,
    get_darwinbox_employee_repository,
    get_ldap_config_repository,
)
from src.api.v1.schemas.darwin_ad_schema import (
    EmployeeDataResponse,
    HierarchyResponse,
    ValidateCredentialResponse,
)
from src.application.services.darwin_ad_service import DarwinAdService
from src.application.services.ldap_service import LdapService
from src.config.settings import settings
from src.domain.repositories.darwinbox_employee_repository import (
    IDarwinboxEmployeeRepository,
)
from src.domain.repositories.ldap_config_repository import ILdapConfigRepository
from src.domain.services.credential_cipher import (
    CredentialDecryptError,
    ICredentialCipher,
)


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Enforce the shared-secret API key when one is configured.

    No-op (open access) when ``DARWIN_PUBLISHED_API_KEY`` is empty, preserving
    drop-in compatibility for callers migrated from the unauthenticated Mendix
    service. Uses a constant-time comparison to avoid timing leaks.
    """
    expected = settings.DARWIN_PUBLISHED_API_KEY
    if not expected:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


router = APIRouter(
    prefix="/adintegratorservices/rest/v1",
    tags=["Darwin AD (Published)"],
    dependencies=[Depends(verify_api_key)],
)


def _get_service(
    repository: IDarwinboxEmployeeRepository = Depends(
        get_darwinbox_employee_repository
    ),
) -> DarwinAdService:
    """FastAPI dependency — builds the Darwin AD read service."""
    return DarwinAdService(repository=repository)


def _get_ldap_service(
    repository: ILdapConfigRepository = Depends(get_ldap_config_repository),
) -> LdapService:
    """FastAPI dependency — builds the LDAP service for credential validation."""
    return LdapService(repository=repository)


@router.get(
    "/getemployees",
    response_model=EmployeeDataResponse,
    summary="Get all employees",
)
async def get_employees(
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Optional employee_status filter, e.g. 'Active'",
    ),
    service: DarwinAdService = Depends(_get_service),
) -> EmployeeDataResponse:
    """Return all stored employees in the Darwin AD ``{employeeData: [...]}`` format."""
    return await service.get_all_employees(status=status_filter)


@router.post(
    "/getselectedemployees",
    response_model=EmployeeDataResponse,
    summary="Get selected employees by ids/emails",
)
async def get_selected_employees(
    EmployeeIDs: str = Form(
        ..., description="Comma-separated employee ids or company emails"
    ),
    service: DarwinAdService = Depends(_get_service),
) -> EmployeeDataResponse:
    """
    Return employees matching the comma-separated identifiers (employee_id or
    company_email_id). Mirrors the Mendix multipart/form-data ``EmployeeIDs`` field.
    """
    identifiers = service.parse_identifiers(EmployeeIDs)
    return await service.get_employees_by_identifiers(identifiers)


@router.post(
    "/getemployeedetails",
    response_model=EmployeeDataResponse,
    summary="Get employee details by ids/emails",
)
async def get_employee_details(
    EmployeeIDs: str = Form(
        ..., description="Comma-separated employee ids or company emails"
    ),
    service: DarwinAdService = Depends(_get_service),
) -> EmployeeDataResponse:
    """
    Return employee details for the comma-separated identifiers (employee_id or
    company_email_id). Same lookup as ``/getselectedemployees``.
    """
    identifiers = service.parse_identifiers(EmployeeIDs)
    return await service.get_employees_by_identifiers(identifiers)


@router.get(
    "/getHierarchyData",
    response_model=HierarchyResponse,
    summary="Get role/designation hierarchy",
)
async def get_hierarchy_data(
    service: DarwinAdService = Depends(_get_service),
) -> HierarchyResponse:
    """
    Build the role/designation hierarchy by walking the manager chain.
    Returns the Mendix ``{"hierarchy": [...]}`` envelope. The Active-only
    filter is controlled by ``settings.DARWIN_HIERARCHY_ACTIVE_CHECK``.
    """
    return await service.get_hierarchy(
        active_only=settings.DARWIN_HIERARCHY_ACTIVE_CHECK
    )


@router.post(
    "/validatecredentials",
    response_model=ValidateCredentialResponse,
    summary="Validate employee credentials against configured LDAP servers",
)
async def validate_credentials(
    EmployeeId: str = Form(...),
    Password: str = Form(...),
    ldap_service: LdapService = Depends(_get_ldap_service),
    cipher: ICredentialCipher = Depends(get_credential_cipher),
) -> ValidateCredentialResponse:
    """
    Validate the given credentials against every enabled LDAP server in turn.

    ``EmployeeId`` and ``Password`` arrive encrypted with the shared key when
    ``DARWIN_VALIDATE_ENCRYPTION_KEY`` is configured; they are decrypted here
    before the bind. With no key configured the cipher is a passthrough and the
    fields are taken as plaintext, so the wire contract is unchanged for callers
    that have not adopted encryption.

    Returns success as soon as any one server accepts the credentials. Response
    matches the legacy Mendix contract (``IsSuccess`` / ``Message`` /
    ``IsValidUser``).
    """
    try:
        username = cipher.decrypt(EmployeeId)
        password = cipher.decrypt(Password)
    except CredentialDecryptError:
        # A bad token is a client/config error, not a server fault. Report it as
        # a failed validation in the legacy response shape rather than a 5xx, and
        # say nothing about which field or why — that would help probe the key.
        return ValidateCredentialResponse(
            IsSuccess=True,
            Message="Invalid username or password",
            IsValidUser=False,
        )

    result = await ldap_service.validate_credentials_across_servers(
        username=username,
        password=password,
    )
    raw = result["raw_response"]

    if result["is_valid_user"]:
        message = f"User validated by '{raw.get('matched_server')}'"
    elif not result["is_success"]:
        message = raw.get("message") or "No LDAP server was reachable to validate the request"
    else:
        message = "Invalid username or password"

    return ValidateCredentialResponse(
        IsSuccess=result["is_success"],
        Message=message,
        IsValidUser=result["is_valid_user"],
    )
