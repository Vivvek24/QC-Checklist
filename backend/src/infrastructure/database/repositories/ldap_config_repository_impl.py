"""
LDAP configuration repository implementation (Adapter).
Implements ILdapConfigRepository using SQLAlchemy async. Supports full CRUD
over multiple LDAP server configurations.
"""

from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.ldap_config import LdapConfig
from src.domain.repositories.ldap_config_repository import ILdapConfigRepository
from src.infrastructure.database.models.ldap_config_model import LdapConfigModel

# Business fields shared between the ORM model and the domain entity.
# Audit fields (id/created_*/modified_*) are handled explicitly.
_FIELDS: tuple[str, ...] = (
    "name",
    "server_uri",
    "base_dn",
    "bind_username",
    "bind_password",
    "domain_prefix",
    "use_ssl",
    "is_enabled",
)


class LdapConfigRepositoryImpl(ILdapConfigRepository):
    """Concrete implementation of LDAP config persistence using SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[LdapConfig]:
        stmt = select(LdapConfigModel).order_by(LdapConfigModel.name.asc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_id(self, config_id: UUID) -> LdapConfig | None:
        model = await self._session.get(LdapConfigModel, config_id)
        return self._to_entity(model) if model else None

    async def get_by_name(self, name: str) -> LdapConfig | None:
        stmt = select(LdapConfigModel).where(LdapConfigModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, config: LdapConfig) -> LdapConfig:
        model = LdapConfigModel(
            id=config.id,
            created_by=config.created_by,
            modified_by=config.modified_by,
            **{name: getattr(config, name) for name in _FIELDS},
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, config: LdapConfig) -> LdapConfig:
        model = await self._session.get(LdapConfigModel, config.id)
        if model is None:
            raise ValueError(f"LDAP config '{config.id}' not found")

        for name in _FIELDS:
            setattr(model, name, getattr(config, name))
        model.modified_by = config.modified_by

        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, config_id: UUID) -> bool:
        stmt = sa_delete(LdapConfigModel).where(LdapConfigModel.id == config_id)
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    @staticmethod
    def _to_entity(model: LdapConfigModel) -> LdapConfig:
        """Map ORM model to domain entity."""
        return LdapConfig(
            id=model.id,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
            **{name: getattr(model, name) for name in _FIELDS},
        )
