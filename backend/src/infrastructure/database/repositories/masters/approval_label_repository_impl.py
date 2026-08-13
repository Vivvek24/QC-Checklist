"""Approval Label Master — repository implementation with junction table."""

from collections import defaultdict
from typing import Any
from sqlalchemy import ColumnElement, Select, delete, func, select
from src.domain.entities.masters.approval_label import ApprovalLabel
from src.domain.repositories.masters.approval_label_repository import IApprovalLabelRepository
from src.infrastructure.database.models.masters.approval_label_model import ApprovalLabelModel, ApprovalLabelUserRoleModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class ApprovalLabelRepositoryImpl(SqlAlchemyRepository[ApprovalLabel, ApprovalLabelModel], IApprovalLabelRepository):
    _model = ApprovalLabelModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(ApprovalLabelModel.label) == code.lower()

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None, stage_id: int | None = None) -> list[ApprovalLabel]:
        stmt = self._f(select(ApprovalLabelModel), search, is_active, stage_id).order_by(ApprovalLabelModel.label).offset(skip).limit(limit)
        return await self._hydrate(list((await self._session.execute(stmt)).scalars().all()))

    async def count(self, search: str | None = None, is_active: bool | None = None, stage_id: int | None = None) -> int:
        return int((await self._session.execute(self._f(select(func.count()).select_from(ApprovalLabelModel), search, is_active, stage_id))).scalar_one())

    async def get_by_id(self, entity_id: int) -> ApprovalLabel | None:
        m = await self._get_model(entity_id)
        if not m: return None
        return (await self._hydrate([m]))[0]

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_label(code, exclude_id)

    async def exists_by_label(self, label: str, exclude_id: int | None = None) -> bool:
        stmt = select(ApprovalLabelModel.id).where(func.lower(ApprovalLabelModel.label) == label.lower())
        if exclude_id: stmt = stmt.where(ApprovalLabelModel.id != exclude_id)
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def exists_by_label_for_stage(self, label: str, stage_id: int, exclude_id: int | None = None) -> bool:
        stmt = select(ApprovalLabelModel.id).where(
            func.lower(ApprovalLabelModel.label) == label.lower(),
            ApprovalLabelModel.stage_id == stage_id,
        )
        if exclude_id:
            stmt = stmt.where(ApprovalLabelModel.id != exclude_id)
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def create(self, entity: ApprovalLabel) -> ApprovalLabel:
        m = ApprovalLabelModel(label=entity.label, stage_id=entity.stage_id, is_active=entity.is_active,
                               created_by=entity.created_by, modified_by=entity.modified_by)
        self._session.add(m); await self._session.flush()
        await self._sync_roles(m.id, entity.role_ids, entity.modified_by)
        return (await self._hydrate([m]))[0]

    async def update(self, entity: ApprovalLabel) -> ApprovalLabel:
        m = await self._require_model(entity.id)
        m.label = entity.label; m.stage_id = entity.stage_id; m.is_active = entity.is_active
        m.modified_by = entity.modified_by; m.modified_date = entity.modified_date
        await self._session.flush()
        await self._sync_roles(entity.id, entity.role_ids, entity.modified_by)
        return (await self._hydrate([m]))[0]

    async def _sync_roles(self, label_id: int, role_ids: list[int], modified_by: str) -> None:
        await self._session.execute(delete(ApprovalLabelUserRoleModel).where(ApprovalLabelUserRoleModel.approval_label_id == label_id))
        for rid in role_ids:
            self._session.add(ApprovalLabelUserRoleModel(approval_label_id=label_id, role_id=rid, created_by=modified_by, modified_by=modified_by))
        await self._session.flush()

    async def _hydrate(self, models: list[ApprovalLabelModel]) -> list[ApprovalLabel]:
        if not models: return []
        ids = [m.id for m in models]
        result = await self._session.execute(
            select(ApprovalLabelUserRoleModel.approval_label_id, ApprovalLabelUserRoleModel.role_id)
            .where(ApprovalLabelUserRoleModel.approval_label_id.in_(ids))
        )
        rm: dict[int, list[int]] = defaultdict(list)
        for row in result.all(): rm[row[0]].append(row[1])
        return [ApprovalLabel(id=m.id, label=m.label, stage_id=m.stage_id, role_ids=rm.get(m.id, []),
                              is_active=m.is_active, created_by=m.created_by, created_date=m.created_date,
                              modified_by=m.modified_by, modified_date=m.modified_date) for m in models]

    @staticmethod
    def _f(stmt: Select[Any], search: str | None, is_active: bool | None, stage_id: int | None = None) -> Select[Any]:
        if search: stmt = stmt.where(ApprovalLabelModel.label.ilike(f"%{search.strip()}%"))
        if is_active is not None: stmt = stmt.where(ApprovalLabelModel.is_active.is_(is_active))
        if stage_id is not None: stmt = stmt.where(ApprovalLabelModel.stage_id == stage_id)
        return stmt

    @staticmethod
    def _to_entity(m: ApprovalLabelModel) -> ApprovalLabel:
        return ApprovalLabel(id=m.id, label=m.label, stage_id=m.stage_id, role_ids=[], is_active=m.is_active,
                             created_by=m.created_by, created_date=m.created_date, modified_by=m.modified_by, modified_date=m.modified_date)
