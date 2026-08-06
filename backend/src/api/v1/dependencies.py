"""
FastAPI dependency injection for API v1.
Provides current user resolution from JWT tokens and service factories.
"""


from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.repositories.approval_matrix_repository import IApprovalMatrixRepository
from src.domain.repositories.audit_log_repository import IAuditLogRepository
from src.domain.repositories.permission_repository import IPermissionRepository
from src.domain.repositories.role_assignment_repository import IRoleAssignmentRepository
from src.domain.repositories.role_repository import IRoleRepository
from src.domain.repositories.user_details_repository import IUserDetailsRepository
from src.domain.repositories.user_repository import IUserRepository
from src.domain.repositories.workflow_definition_repository import (
    IWorkflowDefinitionRepository,
)
from src.domain.repositories.workflow_instance_repository import (
    IWorkflowInstanceRepository,
)
from src.domain.services.password_hasher import IPasswordHasher
from src.domain.services.permission_resolver import IPermissionResolver
from src.infrastructure.database.repositories.approval_matrix_repository_impl import (
    ApprovalMatrixRepositoryImpl,
)
from src.infrastructure.database.repositories.audit_log_repository_impl import (
    AuditLogRepositoryImpl,
)
from src.infrastructure.database.repositories.permission_repository_impl import (
    PermissionRepositoryImpl,
)
from src.infrastructure.database.repositories.role_assignment_repository_impl import (
    RoleAssignmentRepositoryImpl,
)
from src.infrastructure.database.repositories.role_repository_impl import (
    RoleRepositoryImpl,
)
from src.infrastructure.database.repositories.user_details_repository_impl import (
    UserDetailsRepositoryImpl,
)
from src.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)
from src.infrastructure.database.repositories.workflow_definition_repository_impl import (
    WorkflowDefinitionRepositoryImpl,
)
from src.infrastructure.database.repositories.workflow_instance_repository_impl import (
    WorkflowInstanceRepositoryImpl,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.auth_manager import AuthManager
from src.infrastructure.security.jwt_provider import JWTProvider
from src.infrastructure.security.password_hasher_impl import BcryptPasswordHasher

# Bearer token extraction scheme (enables Swagger "Authorize" button)
bearer_scheme = HTTPBearer(auto_error=True)


def get_jwt_provider() -> JWTProvider:
    """Provide JWT provider instance."""
    return JWTProvider()


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IUserRepository:
    """Provide user repository with injected session."""
    return UserRepositoryImpl(session)


def get_workflow_definition_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IWorkflowDefinitionRepository:
    """Provide workflow definition repository with injected session."""
    return WorkflowDefinitionRepositoryImpl(session)


def get_workflow_instance_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IWorkflowInstanceRepository:
    """Provide workflow instance repository with injected session."""
    return WorkflowInstanceRepositoryImpl(session)


def get_approval_matrix_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IApprovalMatrixRepository:
    """Provide approval matrix repository with injected session."""
    return ApprovalMatrixRepositoryImpl(session)


def get_permission_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IPermissionRepository:
    """Provide permission repository with injected session."""
    return PermissionRepositoryImpl(session)


def get_role_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IRoleRepository:
    """Provide role repository with injected session."""
    return RoleRepositoryImpl(session)


def get_role_assignment_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IRoleAssignmentRepository:
    """Provide role assignment repository with injected session."""
    return RoleAssignmentRepositoryImpl(session)


def get_audit_log_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IAuditLogRepository:
    """Provide audit log repository with injected session."""
    return AuditLogRepositoryImpl(session)


def get_permission_resolver(
    session: AsyncSession = Depends(get_db_session),
) -> IPermissionResolver:
    """Provide the effective-permission read model with injected session."""
    from src.infrastructure.security.permission_manager import PermissionManager

    return PermissionManager(session)


def get_user_details_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IUserDetailsRepository:
    """Provide user details repository with injected session."""
    return UserDetailsRepositoryImpl(session)


def get_password_hasher() -> IPasswordHasher:
    """Provide the password hashing service."""
    return BcryptPasswordHasher()


def get_auth_manager(
    user_repo: IUserRepository = Depends(get_user_repository),
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
) -> AuthManager:
    """Provide authentication manager with dependencies."""
    return AuthManager(user_repository=user_repo, jwt_provider=jwt_provider)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
    user_repo: IUserRepository = Depends(get_user_repository),
) -> User:
    """
    Resolve the current authenticated user from the JWT access token.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
        HTTPException 401: If user does not exist.
    """
    try:
        payload = jwt_provider.verify_token(credentials.credentials, expected_type="access")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user = await user_repo.get_by_username(payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure the current user is active and not blocked.

    Raises:
        HTTPException 403: If user is inactive or blocked.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    if current_user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is blocked",
        )
    return current_user
