"""Role and Permission domain entities."""

from dataclasses import dataclass, field
from enum import StrEnum

from src.domain.entities.base_entity import BaseEntity


class PermissionScope(StrEnum):
    MENU = "MENU"
    API = "API"
    FIELD = "FIELD"


class PermissionAction(StrEnum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    APPROVE = "APPROVE"


@dataclass
class Permission(BaseEntity):
    code: str = field(default="")
    name: str = field(default="")
    description: str = field(default="")
    scope: str = field(default=PermissionScope.API)
    resource: str = field(default="")
    action: str = field(default=PermissionAction.READ)
    is_active: bool = field(default=True)


@dataclass
class Role(BaseEntity):
    code: str = field(default="")
    name: str = field(default="")
    description: str = field(default="")
    is_system: bool = field(default=False)
    is_active: bool = field(default=True)
    tenant_id: int | None = field(default=None)
    parent_role_id: int | None = field(default=None)
    permissions: list[Permission] = field(default_factory=list)

    def has_permission(self, permission_code: str) -> bool:
        return any(p.code == permission_code and p.is_active for p in self.permissions)

    def get_permissions_by_scope(self, scope: PermissionScope) -> list[Permission]:
        return [p for p in self.permissions if p.scope == scope and p.is_active]


@dataclass
class RoleAssignment(BaseEntity):
    user_id: int = field(default=0)
    role_id: int = field(default=0)
    tenant_id: int | None = field(default=None)
    is_active: bool = field(default=True)
