"""TestMaster — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.masters.test_master import TestMaster
from src.domain.repositories.masters.test_master_repository import ITestMasterRepository
from src.infrastructure.database.models.masters.test_master_model import TestMasterModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class TestMasterRepositoryImpl(SqlAlchemyRepository[TestMaster, TestMasterModel], ITestMasterRepository):
    _model = TestMasterModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(TestMasterModel.test_name) == code.lower()

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[TestMaster]:
        stmt = self._apply_filters(select(TestMasterModel), search, is_active)
        stmt = stmt.order_by(TestMasterModel.test_name).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = self._apply_filters(select(func.count()).select_from(TestMasterModel), search, is_active)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_by_product(self, product_id: int) -> list[TestMaster]:
        stmt = select(TestMasterModel).where(
            TestMasterModel.product_id == product_id
        ).order_by(TestMasterModel.test_name)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_name(code, exclude_id)

    async def exists_by_name(self, test_name: str, exclude_id: int | None = None) -> bool:
        stmt = select(TestMasterModel.id).where(func.lower(TestMasterModel.test_name) == test_name.lower())
        if exclude_id is not None:
            stmt = stmt.where(TestMasterModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, entity: TestMaster) -> TestMaster:
        model = TestMasterModel(
            test_name=entity.test_name,
            sample_description=entity.sample_description,
            sample_qty=entity.sample_qty,
            product_id=entity.product_id,
            is_active=entity.is_active,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: TestMaster) -> TestMaster:
        model = await self._require_model(entity.id)
        model.test_name = entity.test_name
        model.sample_description = entity.sample_description
        model.sample_qty = entity.sample_qty
        model.product_id = entity.product_id
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search:
            stmt = stmt.where(TestMasterModel.test_name.ilike(f"%{search.strip()}%"))
        if is_active is not None:
            stmt = stmt.where(TestMasterModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(model: TestMasterModel) -> TestMaster:
        return TestMaster(
            id=model.id,
            test_name=model.test_name,
            sample_description=model.sample_description,
            sample_qty=model.sample_qty,
            product_id=model.product_id,
            is_active=model.is_active,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
