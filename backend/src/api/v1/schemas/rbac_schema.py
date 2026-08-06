"""Pydantic schemas for RBAC API endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class PermissionCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    scope: str = Field(..., pattern="^(MENU|API|FIELD)$")
    resource: str = Field(..., min_length=1, max_length=255)
    action: str = Field(..., pattern="^(CREATE|READ|UPDATE|DELETE|EXECUTE|EXPORT|IMPORT|APPROVE)$")


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str
    scope: str
    resource: str
    action: str
    is_active: bool
    created_date: datetime

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    tenant_id: int | None = Field(default=None)
    parent_role_id: int | None = Field(default=None)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    parent_role_id: int | None = Field(default=None)


class RoleResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str
    is_system: bool
    is_active: bool
    tenant_id: int | None
    parent_role_id: int | None
    permissions: list[PermissionResponse] = []
    created_date: datetime
    modified_date: datetime

    model_config = {"from_attributes": True}


class RoleListResponse(BaseModel):
    roles: list[RoleResponse]
    total: int


class RoleAssignRequest(BaseModel):
    user_id: int
    role_id: int
    tenant_id: int | None = Field(default=None)


class RoleRevokeRequest(BaseModel):
    user_id: int
    role_id: int
    tenant_id: int | None = Field(default=None)


class RoleAssignmentResponse(BaseModel):
    id: int
    user_id: int
    role_id: int
    tenant_id: int | None
    is_active: bool
    created_date: datetime

    model_config = {"from_attributes": True}


class PermissionGrantRequest(BaseModel):
    role_id: int
    permission_id: int


class PermissionRevokeRequest(BaseModel):
    role_id: int
    permission_id: int


class MenuPermissionsResponse(BaseModel):
    menu_keys: list[str]
    permissions: list[PermissionResponse]


class ApiPermissionsResponse(BaseModel):
    codes: list[str]
    resource_actions: dict[str, list[str]]
    permissions: list[PermissionResponse]


class FieldPermissionsResponse(BaseModel):
    resource: str
    fields: dict[str, list[str]]


class AuditLogResponse(BaseModel):
    id: int
    actor_id: int | None
    actor_username: str
    action: str
    resource_type: str
    resource_id: str
    tenant_id: int | None
    old_value: str | None
    new_value: str | None
    ip_address: str
    user_agent: str
    extra_data: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int
    skip: int
    limit: int
