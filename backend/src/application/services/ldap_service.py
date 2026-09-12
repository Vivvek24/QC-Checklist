"""
LDAP Application Service.
Orchestrates management of multiple LDAP/Active Directory server
configurations plus per-server health checks and credential validation.

Controllers delegate here; this layer coordinates the external client and the
repository. It contains no protocol or persistence details of its own.
"""

import logging
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException

from src.api.v1.schemas.ldap_schema import (
    LdapConfigCreateRequest,
    LdapConfigListResponse,
    LdapConfigResponse,
    LdapConfigUpdateRequest,
    LdapHealthResponse,
    ValidateLdapCredentialsResponse,
)
from src.domain.entities.ldap_config import LdapConfig
from src.domain.entities.user import User
from src.domain.repositories.ldap_config_repository import ILdapConfigRepository
from src.infrastructure.external.ldap.ldap_client import (
    LdapClient,
    LdapError,
    LdapUnavailableError,
)

logger = logging.getLogger(__name__)


class LdapService:
    """Application service for managing LDAP server configurations."""

    def __init__(self, repository: ILdapConfigRepository) -> None:
        self._repository = repository

    def _build_client(self, config: LdapConfig) -> LdapClient:
        return LdapClient(
            server_uri=config.server_uri,
            base_dn=config.base_dn,
            bind_username=config.bind_username,
            bind_password=config.bind_password,
            domain_prefix=config.domain_prefix,
            use_ssl=config.use_ssl,
        )

    async def _get_or_404(self, config_id: UUID) -> LdapConfig:
        config = await self._repository.get_by_id(config_id)
        if config is None:
            raise HTTPException(status_code=404, detail="LDAP configuration not found")
        return config

    # ─── List ───

    async def list_configs(self) -> LdapConfigListResponse:
        """Return all configured LDAP servers (bind passwords omitted)."""
        configs = await self._repository.list_all()
        return LdapConfigListResponse(
            configs=[self._to_config_response(c) for c in configs],
            total=len(configs),
        )

    async def get_config(self, config_id: UUID) -> LdapConfigResponse:
        """Return a single configuration by id."""
        config = await self._get_or_404(config_id)
        return self._to_config_response(config)

    # ─── Create ───

    async def create_config(
        self, actor: User, request: LdapConfigCreateRequest
    ) -> LdapConfigResponse:
        """Create a new LDAP server configuration."""
        name = request.name.strip()
        if await self._repository.get_by_name(name):
            raise HTTPException(
                status_code=409,
                detail=f"An LDAP configuration named '{name}' already exists",
            )

        entity = LdapConfig(
            id=uuid4(),
            created_by=actor.username,
            modified_by=actor.username,
            name=name,
            server_uri=request.server_uri.strip(),
            base_dn=request.base_dn.strip(),
            bind_username=request.bind_username.strip(),
            bind_password=request.bind_password,
            domain_prefix=request.domain_prefix,
            use_ssl=request.use_ssl,
            is_enabled=request.is_enabled,
        )
        saved = await self._repository.create(entity)
        logger.info("LDAP configuration '%s' created by %s", name, actor.username)
        return self._to_config_response(saved)

    # ─── Update ───

    async def update_config(
        self, actor: User, config_id: UUID, request: LdapConfigUpdateRequest
    ) -> LdapConfigResponse:
        """
        Update an existing LDAP server configuration.

        The bind password is preserved when the request omits it (empty/None),
        so operators can update other fields without re-entering the secret.
        """
        existing = await self._get_or_404(config_id)

        name = request.name.strip()
        conflict = await self._repository.get_by_name(name)
        if conflict and conflict.id != config_id:
            raise HTTPException(
                status_code=409,
                detail=f"An LDAP configuration named '{name}' already exists",
            )

        new_password = (request.bind_password or "").strip()
        password = new_password if new_password else existing.bind_password

        entity = LdapConfig(
            id=existing.id,
            created_by=existing.created_by,
            created_date=existing.created_date,
            modified_by=actor.username,
            name=name,
            server_uri=request.server_uri.strip(),
            base_dn=request.base_dn.strip(),
            bind_username=request.bind_username.strip(),
            bind_password=password,
            domain_prefix=request.domain_prefix,
            use_ssl=request.use_ssl,
            is_enabled=request.is_enabled,
        )
        saved = await self._repository.update(entity)
        logger.info("LDAP configuration '%s' updated by %s", name, actor.username)
        return self._to_config_response(saved)

    # ─── Delete ───

    async def delete_config(self, config_id: UUID) -> None:
        """Delete an LDAP server configuration."""
        await self._get_or_404(config_id)
        await self._repository.delete(config_id)
        logger.info("LDAP configuration '%s' deleted", config_id)

    # ─── Health ───

    async def check_health(self, config_id: UUID) -> LdapHealthResponse:
        """Report whether the given LDAP server is reachable and can be bound."""
        config = await self._get_or_404(config_id)
        client = self._build_client(config)
        result = await client.health_check()
        return LdapHealthResponse(
            id=config.id,
            name=config.name,
            configured=client.is_configured,
            server_uri=config.server_uri,
            status=result.get("status", "unknown"),
            error=result.get("error"),
        )

    # ─── Credential validation ───

    async def validate_credentials(
        self, config_id: UUID, username: str, password: str
    ) -> ValidateLdapCredentialsResponse:
        """
        Validate a user's credentials against the given directory.

        Raises:
            LdapError (and subclasses): propagated from the client for the
                controller to map to an HTTP status.
        """
        config = await self._get_or_404(config_id)
        client = self._build_client(config)
        result = await client.validate_credentials(username, password)
        return ValidateLdapCredentialsResponse(
            is_valid=result.is_valid,
            message=result.message,
            user_dn=result.user_dn,
            attributes=result.attributes,
        )

    async def validate_credentials_across_servers(
        self, username: str, password: str
    ) -> dict[str, Any]:
        """
        Validate a user's credentials against every enabled LDAP server in turn.

        The check short-circuits and returns success as soon as any server
        accepts the credentials. The response mirrors the Darwin AD
        validate-credentials shape (``is_success`` / ``is_valid_user`` /
        ``raw_response``) so existing consumers need no changes.

        - is_success:   True when at least one server gave a definitive answer
                        (valid or invalid), i.e. was reachable.
        - is_valid_user: True when any server accepted the credentials.
        """
        configs = await self._repository.list_all()
        enabled = [c for c in configs if c.is_enabled]

        if not enabled:
            return {
                "is_success": False,
                "is_valid_user": False,
                "raw_response": {
                    "IsSuccess": False,
                    "IsValidUser": False,
                    "message": "No enabled LDAP servers configured",
                    "attempts": [],
                },
            }

        attempts: list[dict[str, Any]] = []
        any_reachable = False

        for config in enabled:
            client = self._build_client(config)
            try:
                result = await client.validate_credentials(username, password)
            except LdapUnavailableError as exc:
                logger.warning("LDAP server '%s' unreachable: %s", config.name, exc.detail)
                attempts.append(
                    {
                        "server": config.name,
                        "reachable": False,
                        "is_valid": False,
                        "error": exc.detail,
                    }
                )
                continue
            except LdapError as exc:
                logger.warning("LDAP error on server '%s': %s", config.name, exc.detail)
                attempts.append(
                    {
                        "server": config.name,
                        "reachable": True,
                        "is_valid": False,
                        "error": exc.detail,
                    }
                )
                continue

            any_reachable = True
            attempts.append(
                {
                    "server": config.name,
                    "reachable": True,
                    "is_valid": result.is_valid,
                    "message": result.message,
                }
            )

            if result.is_valid:
                logger.info(
                    "LDAP credentials for '%s' validated by server '%s'",
                    username,
                    config.name,
                )
                return {
                    "is_success": True,
                    "is_valid_user": True,
                    "raw_response": {
                        "IsSuccess": True,
                        "IsValidUser": True,
                        "matched_server": config.name,
                        "user_dn": result.user_dn,
                        "attributes": result.attributes,
                        "attempts": attempts,
                    },
                }

        logger.info(
            "LDAP credentials for '%s' not validated by any of %d server(s)",
            username,
            len(enabled),
        )
        return {
            "is_success": any_reachable,
            "is_valid_user": False,
            "raw_response": {
                "IsSuccess": any_reachable,
                "IsValidUser": False,
                "matched_server": None,
                "attempts": attempts,
            },
        }

    # ─── Private helpers ───

    @staticmethod
    def _to_config_response(config: LdapConfig) -> LdapConfigResponse:
        """Map a domain entity into the response DTO (omitting the password)."""
        return LdapConfigResponse(
            id=config.id,
            name=config.name,
            server_uri=config.server_uri,
            base_dn=config.base_dn,
            bind_username=config.bind_username,
            domain_prefix=config.domain_prefix,
            use_ssl=config.use_ssl,
            is_enabled=config.is_enabled,
            bind_password_set=bool(config.bind_password),
            created_by=config.created_by,
            created_date=config.created_date,
            modified_by=config.modified_by,
            modified_date=config.modified_date,
        )
