from typing import Any
from sqlalchemy import ColumnElement, Select, func, select
from src.domain.entities.masters.sap_field import SapField
from src.domain.repositories.masters.sap_field_repository import ISapFieldRepository
from src.infrastructure.database.models.masters.sap_field_model import SapFieldModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository

class SapFieldRepositoryImpl(SqlAlchemyRepository[SapField, SapFieldModel], ISapFieldRepository):
    _model = SapFieldModel
    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]: return func.lower(SapFieldModel.field_name) == code.lower()
    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[SapField]:
        stmt = self._f(select(SapFieldModel), search, is_active).order_by(SapFieldModel.field_name).offset(skip).limit(limit)
        return [self._to_entity(m) for m in (await self._session.execute(stmt)).scalars().all()]
    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        return int((await self._session.execute(self._f(select(func.count()).select_from(SapFieldModel), search, is_active))).scalar_one())
    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool: return await self.exists_by_field_name(code, exclude_id)
    async def exists_by_field_name(self, field_name: str, exclude_id: int | None = None) -> bool:
        stmt = select(SapFieldModel.id).where(func.lower(SapFieldModel.field_name) == field_name.lower())
        if exclude_id: stmt = stmt.where(SapFieldModel.id != exclude_id)
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None
    async def create(self, entity: SapField) -> SapField:
        m = SapFieldModel(field_name=entity.field_name, is_active=entity.is_active, created_by=entity.created_by, modified_by=entity.modified_by)
        self._session.add(m); await self._session.flush(); return self._to_entity(m)
    async def update(self, entity: SapField) -> SapField:
        m = await self._require_model(entity.id); m.field_name=entity.field_name; m.is_active=entity.is_active
        m.modified_by=entity.modified_by; m.modified_date=entity.modified_date
        await self._session.flush(); return self._to_entity(m)
    @staticmethod
    def _f(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search: stmt = stmt.where(SapFieldModel.field_name.ilike(f"%{search.strip()}%"))
        if is_active is not None: stmt = stmt.where(SapFieldModel.is_active.is_(is_active))
        return stmt
    @staticmethod
    def _to_entity(m: SapFieldModel) -> SapField:
        return SapField(id=m.id, field_name=m.field_name, is_active=m.is_active, created_by=m.created_by, created_date=m.created_date, modified_by=m.modified_by, modified_date=m.modified_date)
