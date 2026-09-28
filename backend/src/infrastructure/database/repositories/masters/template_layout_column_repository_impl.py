"""Template Layout Column — repository implementation (adapter).

Contains all SQLAlchemy access for the flat TemplateLayoutColumn rows and maps
between ORM models and domain entities. Flushes, never commits — the
request-scoped session owns the transaction boundary.
"""

from sqlalchemy import Delete, Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.masters.template import TemplateLayoutColumn
from src.domain.enums.template_enums import ColumnType
from src.domain.repositories.masters.template_layout_column_repository import (
    ITemplateLayoutColumnRepository,
)
from src.infrastructure.database.models.masters.template_model import (
    TemplateLayoutColumnModel,
)


class TemplateLayoutColumnRepositoryImpl(ITemplateLayoutColumnRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_scope(
        self, format_stage_mapping_id: int, section_id: int | None
    ) -> list[TemplateLayoutColumn]:
        stmt = self._scope_stmt(format_stage_mapping_id, section_id).order_by(
            TemplateLayoutColumnModel.display_order
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_for_stage(self, format_stage_mapping_id: int) -> list[TemplateLayoutColumn]:
        stmt = (
            select(TemplateLayoutColumnModel)
            .where(TemplateLayoutColumnModel.format_stage_mapping_id == format_stage_mapping_id)
            .order_by(TemplateLayoutColumnModel.section_id, TemplateLayoutColumnModel.display_order)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def replace_for_scope(
        self,
        template_id: int,
        format_stage_mapping_id: int,
        section_id: int | None,
        columns: list[TemplateLayoutColumn],
    ) -> list[TemplateLayoutColumn]:
        await self._session.execute(
            self._scope_delete_stmt(format_stage_mapping_id, section_id)
        )

        models = [
            TemplateLayoutColumnModel(
                template_id=template_id,
                format_stage_mapping_id=format_stage_mapping_id,
                section_id=section_id,
                header=col.header,
                column_type=col.column_type.value,
                display_order=col.display_order,
                width=col.width,
                is_required=col.is_required,
                created_by=col.created_by,
                modified_by=col.modified_by,
            )
            for col in columns
        ]
        self._session.add_all(models)
        await self._session.flush()
        return [self._to_entity(m) for m in models]

    async def delete_for_scope(
        self, format_stage_mapping_id: int, section_id: int | None
    ) -> None:
        await self._session.execute(
            self._scope_delete_stmt(format_stage_mapping_id, section_id)
        )
        await self._session.flush()

    @staticmethod
    def _scope_stmt(
        format_stage_mapping_id: int, section_id: int | None
    ) -> Select[tuple[TemplateLayoutColumnModel]]:
        stmt = select(TemplateLayoutColumnModel).where(
            TemplateLayoutColumnModel.format_stage_mapping_id == format_stage_mapping_id
        )
        return (
            stmt.where(TemplateLayoutColumnModel.section_id.is_(None))
            if section_id is None
            else stmt.where(TemplateLayoutColumnModel.section_id == section_id)
        )

    @staticmethod
    def _scope_delete_stmt(
        format_stage_mapping_id: int, section_id: int | None
    ) -> Delete:
        stmt = delete(TemplateLayoutColumnModel).where(
            TemplateLayoutColumnModel.format_stage_mapping_id == format_stage_mapping_id
        )
        return (
            stmt.where(TemplateLayoutColumnModel.section_id.is_(None))
            if section_id is None
            else stmt.where(TemplateLayoutColumnModel.section_id == section_id)
        )

    @staticmethod
    def _to_entity(model: TemplateLayoutColumnModel) -> TemplateLayoutColumn:
        return TemplateLayoutColumn(
            id=model.id,
            template_id=model.template_id,
            format_stage_mapping_id=model.format_stage_mapping_id,
            section_id=model.section_id,
            header=model.header,
            column_type=ColumnType(model.column_type),
            display_order=model.display_order,
            width=model.width,
            is_required=model.is_required,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
