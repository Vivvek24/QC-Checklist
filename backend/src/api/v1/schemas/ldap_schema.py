"""
LDAP service schemas (Pydantic v2).
Request/response DTOs for LDAP server configuration CRUD, health checks, and
credential validation. The bind password is write-only — it is accepted on
create/update but never returned in responses.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class LdapConfigResponse(BaseModel):
    """A stored LDAP server configuration (never includes the bind password)."""

    id: UUID
    name: str
    server_uri: str
    base_dn: str
    bind_username: str
    domain_prefix: str
    use_ssl: bool
    is_enabled: bool
    bind_password_set: bool = Field(
        ..., description="Whether a bind password is currently stored"
    )
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class LdapConfigListResponse(BaseModel):
    """List of configured LDAP servers."""

    configs: list[LdapConfigResponse]
    total: int


class LdapConfigCreateRequest(BaseModel):
    """Request body to create a new LDAP server configuration."""

    name: str = Field(..., min_length=1, description="Unique label, e.g. 'Emcure Pharma'")
    server_uri: str = Field(..., description="e.g. ldap://10.21.91.59:389")
    base_dn: str = Field(default="", description="e.g. DC=emcure,DC=pharma")
    bind_username: str = Field(
        ..., description="Service account, e.g. EPLPHARMA\\93300116"
    )
    bind_password: str = Field(..., description="Service account password")
    domain_prefix: str = Field(
        default="", description="NetBIOS prefix for user binds, e.g. EPLPHARMA\\"
    )
    use_ssl: bool = Field(default=False, description="Use LDAPS/SSL")
    is_enabled: bool = Field(default=True, description="Whether this server is enabled")


class LdapConfigUpdateRequest(BaseModel):
    """Request body to update an LDAP server configuration."""

    name: str = Field(..., min_length=1, description="Unique label")
    server_uri: str = Field(..., description="e.g. ldap://10.21.91.59:389")
    base_dn: str = Field(default="", description="e.g. DC=emcure,DC=pharma")
    bind_username: str = Field(
        ..., description="Service account, e.g. EPLPHARMA\\93300116"
    )
    bind_password: str | None = Field(
        default=None,
        description="Service account password. Leave empty to keep the current one.",
    )
    domain_prefix: str = Field(
        default="", description="NetBIOS prefix for user binds, e.g. EPLPHARMA\\"
    )
    use_ssl: bool = Field(default=False, description="Use LDAPS/SSL")
    is_enabled: bool = Field(default=True, description="Whether this server is enabled")


class LdapHealthResponse(BaseModel):
    """Reachability/health of a configured LDAP server."""

    id: UUID
    name: str
    configured: bool
    server_uri: str
    status: str
    error: str | None = None


class ValidateLdapCredentialsRequest(BaseModel):
    """Request body for LDAP credential validation."""

    username: str = Field(..., description="Username (with or without domain prefix)")
    password: str = Field(..., description="User password")


class ValidateLdapCredentialsResponse(BaseModel):
    """Result of an LDAP credential validation call."""

    is_valid: bool
    message: str = ""
    user_dn: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
