"""Audit Log domain entity. Immutable — never modified after creation."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class AuditAction(StrEnum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ROLE_CREATED = "ROLE_CREATED"
    ROLE_UPDATED = "ROLE_UPDATED"
    ROLE_DELETED = "ROLE_DELETED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REVOKED = "ROLE_REVOKED"
    PERMISSION_CREATED = "PERMISSION_CREATED"
    PERMISSION_UPDATED = "PERMISSION_UPDATED"
    PERMISSION_DELETED = "PERMISSION_DELETED"
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"
    USER_BLOCKED = "USER_BLOCKED"
    USER_UNBLOCKED = "USER_UNBLOCKED"
    USER_ACTIVATED = "USER_ACTIVATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    TOKEN_REFRESHED = "TOKEN_REFRESHED"
    TENANT_CREATED = "TENANT_CREATED"
    TENANT_UPDATED = "TENANT_UPDATED"


@dataclass
class AuditLog:
    """
    Immutable audit log entry. id is DB-generated (BIGSERIAL), default 0.
    actor_id and tenant_id are BigInt FKs (int), not UUIDs.
    """

    id: int = field(default=0)
    actor_id: int | None = field(default=None)
    actor_username: str = field(default="system")
    action: str = field(default="")
    resource_type: str = field(default="")
    resource_id: str = field(default="")
    tenant_id: int | None = field(default=None)
    old_value: str | None = field(default=None)
    new_value: str | None = field(default=None)
    ip_address: str = field(default="")
    user_agent: str = field(default="")
    extra_data: str | None = field(default=None)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
