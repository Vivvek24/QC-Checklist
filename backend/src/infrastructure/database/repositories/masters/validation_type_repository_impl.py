from typing import Any
from sqlalchemy import ColumnElement, Select, func, select
from src.domain.entities.masters.validation_type import ValidationType
from src.domain.repositories.masters.validation_type_repository import IValidationTypeRepository
from src.infrastructure.database.models.masters.validation_type_model import ValidationTypeModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository

class ValidationTypeRepositoryImpl(SqlAlchemyRepository[ValidationType, ValidationTypeModel], IValidationTypeRepository):
    _model = ValidationTypeModel
    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]: return func.lower(ValidationTypeModel.name) == code.lower()
    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[ValidationType]:
        stmt = self._f(select(ValidationTypeModel), search, is_active).order_by(ValidationTypeModel.name).offset(skip).limit(limit)
        return [self._to_entity(m) for m in (await self._session.execute(stmt)).scalars().all()]
    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        return int((await self._session.execute(self._f(select(func.count()).select_from(ValidationTypeModel), search, is_active))).scalar_one())
    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool: return await self.exists_by_name(code, exclude_id)
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool:
        stmt = select(ValidationTypeModel.id).where(func.lower(ValidationTypeModel.name) == name.lower())
        if exclude_id: stmt = stmt.where(ValidationTypeModel.id != exclude_id)
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None
    async def create(self, entity: ValidationType) -> ValidationType:
        m = ValidationTypeModel(name=entity.name, is_active=entity.is_active, created_by=entity.created_by, modified_by=entity.modified_by)
        self._session.add(m); await self._session.flush(); return self._to_entity(m)
    async def update(self, entity: ValidationType) -> ValidationType:
        m = await self._require_model(entity.id); m.name=entity.name; m.is_active=entity.is_active; m.modified_by=entity.modified_by; m.modified_date=entity.modified_date
        await self._session.flush(); return self._to_entity(m)
    @staticmethod
    def _f(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search: stmt = stmt.where(ValidationTypeModel.name.ilike(f"%{search.strip()}%"))
        if is_active is not None: stmt = stmt.where(ValidationTypeModel.is_active.is_(is_active))
        return stmt
    @staticmethod
    def _to_entity(m: ValidationTypeModel) -> ValidationType:
        return ValidationType(id=m.id, name=m.name, is_active=m.is_active, created_by=m.created_by, created_date=m.created_date, modified_by=m.modified_by, modified_date=m.modified_date)
