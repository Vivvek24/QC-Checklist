"""Remark Master — repository implementation with junction table."""

from collections import defaultdict
from typing import Any

from sqlalchemy import ColumnElement, Select, delete, func, select

from src.domain.entities.masters.remark import Remark
from src.domain.repositories.masters.remark_repository import IRemarkRepository
from src.infrastructure.database.models.masters.remark_model import RemarkModel, RemarkUserRoleModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class RemarkRepositoryImpl(SqlAlchemyRepository[Remark, RemarkModel], IRemarkRepository):
    _model = RemarkModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(RemarkModel.remark) == code.lower()

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[Remark]:
        stmt = self._f(select(RemarkModel), search, is_active).order_by(RemarkModel.id.desc()).offset(skip).limit(limit)
        models = list((await self._session.execute(stmt)).scalars().all())
        return await self._hydrate(models)

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        return int((await self._session.execute(self._f(select(func.count()).select_from(RemarkModel), search, is_active))).scalar_one())

    async def get_by_id(self, entity_id: int) -> Remark | None:
        model = await self._get_model(entity_id)
        if model is None:
            return None
        return (await self._hydrate([model]))[0]

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_remark(code, exclude_id)

    async def exists_by_remark(self, remark: str, exclude_id: int | None = None) -> bool:
        stmt = select(RemarkModel.id).where(func.lower(RemarkModel.remark) == remark.lower())
        if exclude_id:
            stmt = stmt.where(RemarkModel.id != exclude_id)
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def create(self, entity: Remark) -> Remark:
        model = RemarkModel(remark=entity.remark, is_active=entity.is_active,
                            created_by=entity.created_by, modified_by=entity.modified_by)
        self._session.add(model)
        await self._session.flush()
        # Insert junction rows
        await self._sync_roles(model.id, entity.role_ids, entity.modified_by)
        entity.id = model.id
        return (await self._hydrate([model]))[0]

    async def update(self, entity: Remark) -> Remark:
        model = await self._require_model(entity.id)
        model.remark = entity.remark
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        await self._sync_roles(entity.id, entity.role_ids, entity.modified_by)
        return (await self._hydrate([model]))[0]

    async def _sync_roles(self, remark_id: int, role_ids: list[int], modified_by: str) -> None:
        """Replace all junction rows for this remark with the new set."""
        await self._session.execute(delete(RemarkUserRoleModel).where(RemarkUserRoleModel.remark_id == remark_id))
        for role_id in role_ids:
            self._session.add(RemarkUserRoleModel(
                remark_id=remark_id, role_id=role_id,
                created_by=modified_by, modified_by=modified_by,
            ))
        await self._session.flush()

    async def _hydrate(self, models: list[RemarkModel]) -> list[Remark]:
        """Attach role_ids to each remark."""
        if not models:
            return []
        ids = [m.id for m in models]
        result = await self._session.execute(
            select(RemarkUserRoleModel.remark_id, RemarkUserRoleModel.role_id)
            .where(RemarkUserRoleModel.remark_id.in_(ids))
        )
        roles_map: dict[int, list[int]] = defaultdict(list)
        for row in result.all():
            roles_map[row[0]].append(row[1])

        return [
            Remark(
                id=m.id, remark=m.remark, role_ids=roles_map.get(m.id, []),
                is_active=m.is_active, created_by=m.created_by, created_date=m.created_date,
                modified_by=m.modified_by, modified_date=m.modified_date,
            )
            for m in models
        ]

    @staticmethod
    def _f(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search:
            stmt = stmt.where(RemarkModel.remark.ilike(f"%{search.strip()}%"))
        if is_active is not None:
            stmt = stmt.where(RemarkModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(m: RemarkModel) -> Remark:
        # Basic mapping without roles — _hydrate adds them
        return Remark(id=m.id, remark=m.remark, role_ids=[], is_active=m.is_active,
                      created_by=m.created_by, created_date=m.created_date,
                      modified_by=m.modified_by, modified_date=m.modified_date)
