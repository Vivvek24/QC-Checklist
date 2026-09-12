"""
LDAP configuration domain entity.
Represents a single LDAP/Active Directory server configuration. Multiple
configurations can be stored and managed; each is used to validate user
credentials against its corresponding directory.
"""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity


@dataclass
class LdapConfig(BaseEntity):
    """
    LDAP connection configuration aggregate.

    Business Rules:
    - ``name`` is a human-friendly unique label for the server configuration.
    - ``bind_password`` is the service-account secret and must never be exposed
      through API responses.
    """

    name: str = field(default="")
    server_uri: str = field(default="")
    base_dn: str = field(default="")
    bind_username: str = field(default="")
    bind_password: str = field(default="")
    domain_prefix: str = field(default="")
    use_ssl: bool = field(default=False)
    is_enabled: bool = field(default=True)

    @property
    def is_configured(self) -> bool:
        """True when the minimum fields needed to attempt a bind are present."""
        return bool(self.server_uri and self.bind_username and self.bind_password)
