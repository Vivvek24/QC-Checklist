"""Format Master — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.masters.format import Format
from src.domain.enums.format_enums import FormatType
from src.domain.repositories.masters.format_repository import IFormatRepository
from src.infrastructure.database.models.masters.format_model import FormatModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class FormatRepositoryImpl(
    SqlAlchemyRepository[Format, FormatModel],
    IFormatRepository,
):
    _model = FormatModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return func.lower(FormatModel.format_no) == code.lower()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[Format]:
        stmt = self._apply_filters(select(FormatModel), search, is_active)
        stmt = stmt.order_by(FormatModel.format_no).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = self._apply_filters(select(func.count()).select_from(FormatModel), search, is_active)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return await self.exists_by_format_no(code, exclude_id)

    async def exists_by_format_no(self, format_no: str, exclude_id: int | None = None) -> bool:
        stmt = select(FormatModel.id).where(func.lower(FormatModel.format_no) == format_no.lower())
        if exclude_id is not None:
            stmt = stmt.where(FormatModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, entity: Format) -> Format:
        model = FormatModel(
            format_no=entity.format_no,
            format_title=entity.format_title,
            format_name=entity.format_name,
            unit_id=entity.unit_id,
            format_type=entity.format_type.value,
            has_declaration_question=entity.has_declaration_question,
            is_active=entity.is_active,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: Format) -> Format:
        model = await self._require_model(entity.id)
        model.format_no = entity.format_no
        model.format_title = entity.format_title
        model.format_name = entity.format_name
        model.unit_id = entity.unit_id
        model.format_type = entity.format_type.value
        model.has_declaration_question = entity.has_declaration_question
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if search:
            pattern = f"%{search.strip()}%"
            from sqlalchemy import or_
            stmt = stmt.where(or_(
                FormatModel.format_no.ilike(pattern),
                FormatModel.format_title.ilike(pattern),
                FormatModel.format_name.ilike(pattern),
            ))
        if is_active is not None:
            stmt = stmt.where(FormatModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(model: FormatModel) -> Format:
        return Format(
            id=model.id,
            format_no=model.format_no,
            format_title=model.format_title,
            format_name=model.format_name,
            unit_id=model.unit_id,
            format_type=FormatType(model.format_type),
            has_declaration_question=model.has_declaration_question,
            is_active=model.is_active,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
