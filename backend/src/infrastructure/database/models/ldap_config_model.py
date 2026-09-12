"""
SQLAlchemy ORM model for LDAP server configurations.
Maps to the 'ldap_config' table which holds one row per configured
LDAP/Active Directory server used for validating user credentials.

The bind password is stored so the service account can authenticate for
health checks and lookups. It is never returned through API responses.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class LdapConfigModel(BaseModel):
    """LDAP configuration table — one row per configured LDAP server."""

    __tablename__ = "ldap_config"

    name: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True, default=""
    )
    server_uri: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    base_dn: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    bind_username: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    bind_password: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    domain_prefix: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
