"""
LDAP / Active Directory integration client.

Validates user credentials against a corporate LDAP/AD server by attempting a
bind. Also supports a health check that binds with the configured service
account.

Uses the synchronous ``ldap3`` library; blocking calls are dispatched to a
worker thread via ``asyncio.to_thread`` so the async event loop is not blocked.
No business logic — only LDAP protocol interaction. Mirrors the exception
hierarchy used by the other external clients (EmployeeADClient / DarwinboxClient).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from ldap3 import ALL, Connection, Server
from ldap3.core.exceptions import (
    LDAPBindError,
    LDAPException,
    LDAPInvalidCredentialsResult,
    LDAPSocketOpenError,
)

logger = logging.getLogger(__name__)


class LdapError(Exception):
    """Base class for LDAP adapter errors."""

    def __init__(self, detail: str = "LDAP service error") -> None:
        super().__init__(detail)
        self.detail = detail


class LdapAuthError(LdapError):
    """The service account credentials were rejected by the directory."""

    def __init__(self, detail: str = "LDAP authentication failed") -> None:
        super().__init__(detail)


class LdapUnavailableError(LdapError):
    """The LDAP server could not be reached."""

    def __init__(self, detail: str = "LDAP service unavailable") -> None:
        super().__init__(detail)


@dataclass(frozen=True)
class LdapValidationResult:
    """Parsed result of an LDAP credential validation call."""

    is_valid: bool
    message: str = ""
    user_dn: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)


class LdapClient:
    """Client for validating credentials against an LDAP/AD directory."""

    def __init__(
        self,
        server_uri: str,
        base_dn: str,
        bind_username: str,
        bind_password: str,
        domain_prefix: str = "",
        use_ssl: bool = False,
        timeout: int = 10,
    ) -> None:
        self._server_uri = (server_uri or "").strip()
        self._base_dn = (base_dn or "").strip()
        self._bind_username = (bind_username or "").strip()
        self._bind_password = bind_password or ""
        self._domain_prefix = (domain_prefix or "").strip()
        self._use_ssl = use_ssl
        self._timeout = timeout

    @property
    def server_uri(self) -> str:
        return self._server_uri

    @property
    def is_configured(self) -> bool:
        """True when the minimum fields needed to attempt a bind are present."""
        return bool(self._server_uri and self._bind_username and self._bind_password)

    def _build_server(self) -> Server:
        return Server(
            self._server_uri,
            use_ssl=self._use_ssl,
            get_info=ALL,
            connect_timeout=self._timeout,
        )

    def _qualify_username(self, username: str) -> str:
        """
        Prepend the NetBIOS domain prefix unless the username already carries a
        domain (``DOMAIN\\user``) or is a UPN (``user@domain``).
        """
        username = (username or "").strip()
        if "\\" in username or "@" in username:
            return username
        return f"{self._domain_prefix}{username}"

    # ─── Health ───

    async def health_check(self) -> dict[str, Any]:
        """
        Attempt to reach the server and bind with the service account.

        Returns a dict describing reachability; never raises.
        """
        if not self.is_configured:
            return {
                "status": "not_configured",
                "url": self._server_uri,
                "error": "LDAP configuration is incomplete",
            }
        return await asyncio.to_thread(self._health_check_sync)

    def _health_check_sync(self) -> dict[str, Any]:
        try:
            server = self._build_server()
            conn = Connection(
                server,
                user=self._bind_username,
                password=self._bind_password,
                auto_bind=True,
                receive_timeout=self._timeout,
            )
            conn.unbind()
            return {"status": "reachable", "url": self._server_uri}
        except LDAPInvalidCredentialsResult as exc:
            logger.warning("LDAP service-account bind rejected: %s", exc)
            return {
                "status": "auth_failed",
                "url": self._server_uri,
                "error": "Service account credentials were rejected",
            }
        except (LDAPBindError, LDAPSocketOpenError) as exc:
            logger.error("LDAP server unreachable/bind error: %s", exc)
            return {"status": "unreachable", "url": self._server_uri, "error": str(exc)}
        except LDAPException as exc:  # pragma: no cover - defensive
            logger.error("LDAP health check error: %s", exc)
            return {"status": "error", "url": self._server_uri, "error": str(exc)}

    # ─── Credential validation ───

    async def validate_credentials(
        self, username: str, password: str
    ) -> LdapValidationResult:
        """
        Validate an end-user's credentials by attempting an LDAP bind as that user.

        Returns:
            LdapValidationResult with ``is_valid`` True on a successful bind, or
            False when the directory rejects the credentials.

        Raises:
            LdapUnavailableError: the server could not be reached.
            LdapError: any other unexpected LDAP failure.
        """
        if not self._server_uri:
            raise LdapError("LDAP server is not configured")
        if not password:
            # Anonymous/unauthenticated binds must not count as valid.
            return LdapValidationResult(is_valid=False, message="Password is required")
        return await asyncio.to_thread(
            self._validate_credentials_sync, username, password
        )

    def _validate_credentials_sync(
        self, username: str, password: str
    ) -> LdapValidationResult:
        user_identifier = self._qualify_username(username)
        logger.info("Validating LDAP credentials for: %s", user_identifier)
        try:
            server = self._build_server()
            conn = Connection(
                server,
                user=user_identifier,
                password=password,
                auto_bind=True,
                receive_timeout=self._timeout,
            )
        except LDAPInvalidCredentialsResult:
            logger.info("LDAP credentials rejected for: %s", user_identifier)
            return LdapValidationResult(
                is_valid=False, message="Invalid username or password"
            )
        except LDAPBindError as exc:
            logger.info("LDAP bind failed for %s: %s", user_identifier, exc)
            return LdapValidationResult(
                is_valid=False, message="Invalid username or password"
            )
        except LDAPSocketOpenError as exc:
            logger.error("LDAP server unreachable: %s", exc)
            raise LdapUnavailableError(str(exc)) from exc
        except LDAPException as exc:
            logger.error("LDAP error during validation: %s", exc)
            raise LdapError(str(exc)) from exc

        # Bind succeeded — optionally look up a few descriptive attributes.
        attributes: dict[str, Any] = {}
        user_dn = ""
        try:
            sam = username.split("\\")[-1].split("@")[0].strip()
            if (
                self._base_dn
                and conn.search(
                    self._base_dn,
                    f"(sAMAccountName={sam})",
                    attributes=["cn", "displayName", "mail", "userPrincipalName"],
                )
                and conn.entries
            ):
                entry = conn.entries[0]
                user_dn = entry.entry_dn
                attributes = {
                    k: str(v) for k, v in entry.entry_attributes_as_dict.items()
                }
        except LDAPException as exc:  # pragma: no cover - lookup is best-effort
            logger.debug("LDAP attribute lookup skipped: %s", exc)
        finally:
            conn.unbind()

        return LdapValidationResult(
            is_valid=True,
            message="Credentials are valid",
            user_dn=user_dn,
            attributes=attributes,
        )
