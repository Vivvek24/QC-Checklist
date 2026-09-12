"""
FastAPI dependency injection for API v1.
Provides current user resolution from JWT tokens and service factories.
"""


from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.employee_import_writer import IEmployeeImportWriter
from src.domain.entities.user import User
from src.domain.repositories.audit_log_repository import IAuditLogRepository
from src.domain.repositories.darwinbox_employee_repository import (
    IDarwinboxEmployeeRepository,
)
from src.domain.repositories.ldap_config_repository import ILdapConfigRepository
from src.domain.repositories.permission_repository import IPermissionRepository
from src.domain.repositories.role_assignment_repository import IRoleAssignmentRepository
from src.domain.repositories.role_repository import IRoleRepository
from src.domain.repositories.user_details_repository import IUserDetailsRepository
from src.domain.repositories.user_repository import IUserRepository
from src.domain.services.credential_cipher import ICredentialCipher
from src.domain.services.password_hasher import IPasswordHasher
from src.domain.services.permission_resolver import IPermissionResolver

if TYPE_CHECKING:
    # Import-time only: both adapters import `get_current_active_user` (directly or
    # transitively) from this module for their dependency factories, so a runtime
    # import here would be circular. The factories below import them lazily.
    from src.infrastructure.security.audit_service import AuditService
from src.config.settings import settings
from src.infrastructure.database.audit_context import set_audit_actor
from src.infrastructure.database.repositories.audit_log_repository_impl import (
    AuditLogRepositoryImpl,
)
from src.infrastructure.database.repositories.darwinbox_employee_repository_impl import (
    DarwinboxEmployeeRepositoryImpl,
)
from src.infrastructure.database.repositories.employee_import_writer_impl import (
    EmployeeImportWriterImpl,
)
from src.infrastructure.database.repositories.ldap_config_repository_impl import (
    LdapConfigRepositoryImpl,
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
from src.infrastructure.database.session import get_db_session
from src.infrastructure.database.unit_of_work import UnitOfWork
from src.infrastructure.security.auth_manager import AuthManager
from src.infrastructure.security.credential_cipher_impl import (
    FernetCredentialCipher,
    PassthroughCredentialCipher,
)
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


def get_darwinbox_employee_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IDarwinboxEmployeeRepository:
    """Provide Darwinbox employee repository with injected session."""
    return DarwinboxEmployeeRepositoryImpl(session)


def get_ldap_config_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ILdapConfigRepository:
    """Provide LDAP configuration repository with injected session."""
    return LdapConfigRepositoryImpl(session)


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

    # Stage 2 of the audit context: AuditContextMiddleware seeded IP/user-agent
    # but runs before dependencies, so it has no authenticated user to record.
    # This dependency shares a task context with the route handler and its
    # database session, so the value is visible to the audit listener at flush
    # time.
    #
    # tenant_id is not set — users are not yet scoped to a tenant. Add it here
    # once UserModel carries one.
    set_audit_actor(actor_id=user.id, actor_username=user.username)

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


# ─── RBAC / audit repository factories ───
# These are the one place a session is turned into a repository. Services and
# controllers depend on the port, never on the session.


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


def get_user_details_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IUserDetailsRepository:
    """Provide user details repository with injected session."""
    return UserDetailsRepositoryImpl(session)


def get_permission_resolver(
    session: AsyncSession = Depends(get_db_session),
) -> IPermissionResolver:
    """
    Provide the effective-permission read model with injected session.

    Imported lazily: `permission_manager` imports `get_current_active_user` from
    this module for its `require_*` dependency factories, so a module-level
    import here would be circular.
    """
    from src.infrastructure.security.permission_manager import PermissionManager

    return PermissionManager(session)


def get_password_hasher() -> IPasswordHasher:
    """Provide the password hashing adapter. No session needed — pure CPU work."""
    return BcryptPasswordHasher()


def get_credential_cipher() -> ICredentialCipher:
    """
    Provide the cipher that decrypts the published `validatecredentials` inputs.

    Returns a Fernet-backed cipher when `DARWIN_VALIDATE_ENCRYPTION_KEY` is set,
    otherwise a passthrough that accepts plaintext — the same opt-in-by-config
    stance the endpoint's `X-API-Key` check takes, so turning encryption on is one
    env var and does not change the wire contract for callers that adopt it.
    """
    key = settings.DARWIN_VALIDATE_ENCRYPTION_KEY
    if not key:
        return PassthroughCredentialCipher()
    return FernetCredentialCipher(key)


def get_employee_import_writer(
    session: AsyncSession = Depends(get_db_session),
    user_repo: IUserRepository = Depends(get_user_repository),
    user_details_repo: IUserDetailsRepository = Depends(get_user_details_repository),
) -> IEmployeeImportWriter:
    """
    Provide the employee-import writer, attached to the request's own session.

    `UnitOfWork.from_session(session)` rather than `UnitOfWork()`: the request-scoped
    session from `get_db_session` still owns the commit at the end of the request; this
    writer only needs `savepoint()` from the unit of work, not a second transaction.
    Both repositories are bound to that same session, so the savepoint covers their
    writes too.
    """
    return EmployeeImportWriterImpl(
        UnitOfWork.from_session(session), user_repo, user_details_repo
    )


def get_audit_service(
    session: AsyncSession = Depends(get_db_session),
) -> "AuditService":
    """
    Provide the audit-writing service with injected session.

    Same shape as `get_permission_resolver`: an infrastructure adapter that needs
    the request's session is built once here, so controllers depend on the factory
    instead of importing `AuditService` and constructing it inline.
    """
    from src.infrastructure.security.audit_service import AuditService

    return AuditService(session)
