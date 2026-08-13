"""
User management API endpoints.
Thin controller — maps HTTP schemas to/from application DTOs, delegates to UserService.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.v1.dependencies import (
    get_audit_log_repository,
    get_current_active_user,
    get_password_hasher,
    get_role_assignment_repository,
    get_role_repository,
    get_user_details_repository,
    get_user_repository,
)
from src.api.v1.schemas.user_request import CreateUserRequest, UpdateUserRequest
from src.api.v1.schemas.user_response import UserDetailResponse, UserListResponse, UserResponse
from src.application.dtos.user_dtos import CreateUserDTO, UpdateUserDTO
from src.application.services.user_service import UserService
from src.domain.entities.user import User
from src.domain.repositories.audit_log_repository import IAuditLogRepository
from src.domain.repositories.role_assignment_repository import IRoleAssignmentRepository
from src.domain.repositories.role_repository import IRoleRepository
from src.domain.repositories.user_details_repository import IUserDetailsRepository
from src.domain.repositories.user_repository import IUserRepository
from src.domain.services.password_hasher import IPasswordHasher
from src.infrastructure.security.permission_manager import require_api_permission

router = APIRouter(prefix="/users", tags=["Users"])


def _get_user_service(
    user_repo: IUserRepository = Depends(get_user_repository),
    user_details_repo: IUserDetailsRepository = Depends(get_user_details_repository),
    role_repo: IRoleRepository = Depends(get_role_repository),
    assignment_repo: IRoleAssignmentRepository = Depends(get_role_assignment_repository),
    audit_repo: IAuditLogRepository = Depends(get_audit_log_repository),
    password_hasher: IPasswordHasher = Depends(get_password_hasher),
) -> UserService:
    return UserService(
        user_repo=user_repo,
        user_details_repo=user_details_repo,
        role_repo=role_repo,
        assignment_repo=assignment_repo,
        audit_repo=audit_repo,
        password_hasher=password_hasher,
    )


@router.get(
    "",
    response_model=UserListResponse,
    summary="List all users",
    dependencies=[Depends(require_api_permission("users", "READ"))],
)
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    service: UserService = Depends(_get_user_service),
) -> UserListResponse:
    """GET /api/v1/users"""
    result = await service.list_users(skip=skip, limit=limit)
    return UserListResponse(
        users=[
            UserResponse(
                id=u.id, username=u.username, is_active=u.is_active,
                is_blocked=u.is_blocked, is_validate_ad=u.is_validate_ad,
                employee_id=u.employee_id, employee_name=u.employee_name,
                email=u.email, last_login=u.last_login,
                created_by=u.created_by, created_date=u.created_date,
                modified_by=u.modified_by, modified_date=u.modified_date,
            )
            for u in result.users
        ],
        total=result.total,
        skip=result.skip,
        limit=result.limit,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    dependencies=[Depends(require_api_permission("users", "CREATE"))],
)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(_get_user_service),
) -> UserResponse:
    """POST /api/v1/users"""
    try:
        dto = CreateUserDTO(
            username=request.username,
            password=request.password,
            is_validate_ad=request.is_validate_ad,
            role_id=request.role_id,
        )
        result = await service.create_user(dto=dto, actor=current_user)
        return UserResponse(
            id=result.id, username=result.username, is_active=result.is_active,
            is_blocked=result.is_blocked, is_validate_ad=result.is_validate_ad,
            employee_id=result.employee_id, employee_name=result.employee_name,
            email=result.email, last_login=result.last_login,
            created_by=result.created_by, created_date=result.created_date,
            modified_by=result.modified_by, modified_date=result.modified_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(_get_user_service),
) -> UserResponse:
    """GET /api/v1/users/{user_id}"""
    try:
        user = await service.get_user(user_id)
        return UserResponse(
            id=user.id, username=user.username, is_active=user.is_active,
            is_blocked=user.is_blocked, is_validate_ad=user.is_validate_ad,
            created_by=user.created_by, created_date=user.created_date,
            modified_by=user.modified_by, modified_date=user.modified_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    dependencies=[Depends(require_api_permission("users", "UPDATE"))],
)
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(_get_user_service),
) -> UserResponse:
    """PATCH /api/v1/users/{user_id}"""
    try:
        dto = UpdateUserDTO(
            is_active=request.is_active,
            is_blocked=request.is_blocked,
            is_validate_ad=request.is_validate_ad,
            role_id=request.role_id,
            email=request.email,
            password=request.password,
        )
        result = await service.update_user(user_id=user_id, dto=dto, actor=current_user)
        return UserResponse(
            id=result.id, username=result.username, is_active=result.is_active,
            is_blocked=result.is_blocked, is_validate_ad=result.is_validate_ad,
            employee_id=result.employee_id, employee_name=result.employee_name,
            email=result.email, last_login=result.last_login,
            created_by=result.created_by, created_date=result.created_date,
            modified_by=result.modified_by, modified_date=result.modified_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{user_id}/details",
    response_model=UserDetailResponse,
    summary="Get full user details (all employee AD fields)",
)
async def get_user_details(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(_get_user_service),
) -> UserDetailResponse:
    """GET /api/v1/users/{user_id}/details"""
    try:
        result = await service.get_user_details(user_id)
        return UserDetailResponse(**result.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{user_id}/roles",
    summary="Get roles assigned to a user",
)
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(_get_user_service),
) -> dict[str, Any]:
    """GET /api/v1/users/{user_id}/roles"""
    return await service.get_user_roles(user_id)


@router.get(
    "/{user_id}/login-history",
    summary="Get login/logout history for a user",
)
async def get_user_login_history(
    user_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(_get_user_service),
) -> list[dict[str, Any]]:
    """GET /api/v1/users/{user_id}/login-history"""
    return await service.get_login_history(user_id=user_id, limit=limit)

