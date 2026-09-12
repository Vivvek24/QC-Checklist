"""
LDAP configuration repository interface (Port).
Defines the contract for persisting LDAP server configuration records.
The domain layer owns this interface; infrastructure implements it.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.ldap_config import LdapConfig


class ILdapConfigRepository(ABC):
    """Abstract repository for LdapConfig records (multiple servers)."""

    @abstractmethod
    async def list_all(self) -> list[LdapConfig]:
        """Return all configured LDAP servers ordered by name."""
        ...

    @abstractmethod
    async def get_by_id(self, config_id: UUID) -> LdapConfig | None:
        """Retrieve a configuration by its id, or None if not found."""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> LdapConfig | None:
        """Retrieve a configuration by its unique name, or None if not found."""
        ...

    @abstractmethod
    async def create(self, config: LdapConfig) -> LdapConfig:
        """Persist a new LDAP server configuration."""
        ...

    @abstractmethod
    async def update(self, config: LdapConfig) -> LdapConfig:
        """Update an existing LDAP server configuration."""
        ...

    @abstractmethod
    async def delete(self, config_id: UUID) -> bool:
        """Delete a configuration by id. Returns True if a row was removed."""
        ...
