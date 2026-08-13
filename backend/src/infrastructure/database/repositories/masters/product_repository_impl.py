"""Product Master — repository implementation."""

from typing import Any
from sqlalchemy import ColumnElement, Select, func, select
from src.domain.entities.masters.product import Product
from src.domain.repositories.masters.product_repository import IProductRepository
from src.infrastructure.database.models.masters.product_model import ProductModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class ProductRepositoryImpl(SqlAlchemyRepository[Product, ProductModel], IProductRepository):
    _model = ProductModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(ProductModel.product_name) == code.lower()

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[Product]:
        stmt = self._apply_filters(select(ProductModel), search, is_active).order_by(ProductModel.product_name).offset(skip).limit(limit)
        return [self._to_entity(m) for m in (await self._session.execute(stmt)).scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        return int((await self._session.execute(self._apply_filters(select(func.count()).select_from(ProductModel), search, is_active))).scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_name(code, exclude_id)

    async def exists_by_name(self, product_name: str, exclude_id: int | None = None) -> bool:
        stmt = select(ProductModel.id).where(func.lower(ProductModel.product_name) == product_name.lower())
        if exclude_id: stmt = stmt.where(ProductModel.id != exclude_id)
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def create(self, entity: Product) -> Product:
        model = ProductModel(product_name=entity.product_name, storage_conditions=entity.storage_conditions,
                             is_active=entity.is_active, created_by=entity.created_by, modified_by=entity.modified_by)
        self._session.add(model); await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: Product) -> Product:
        model = await self._require_model(entity.id)
        model.product_name = entity.product_name
        model.storage_conditions = entity.storage_conditions
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by; model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search: stmt = stmt.where(ProductModel.product_name.ilike(f"%{search.strip()}%"))
        if is_active is not None: stmt = stmt.where(ProductModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(m: ProductModel) -> Product:
        return Product(id=m.id, product_name=m.product_name, storage_conditions=m.storage_conditions,
                       is_active=m.is_active, created_by=m.created_by, created_date=m.created_date,
                       modified_by=m.modified_by, modified_date=m.modified_date)
