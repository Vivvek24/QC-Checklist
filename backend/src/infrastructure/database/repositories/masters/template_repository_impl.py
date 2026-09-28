"""Template — repository implementation (adapter).

Contains all SQLAlchemy access for the Template aggregate and maps between
ORM models and domain entities. Flushes, never commits — the request-scoped
session owns the transaction boundary.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.masters.template import Template
from src.domain.repositories.masters.template_repository import ITemplateRepository
from src.infrastructure.database.models.masters.template_model import TemplateModel


class TemplateRepositoryImpl(ITemplateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, template_id: int) -> Template | None:
        model = await self._session.get(TemplateModel, template_id)
        return self._to_entity(model) if model else None

    async def get_by_format_id(self, format_id: int) -> Template | None:
        stmt = select(TemplateModel).where(TemplateModel.format_id == format_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, template: Template) -> Template:
        model = TemplateModel(
            format_id=template.format_id,
            is_active=template.is_active,
            created_by=template.created_by,
            modified_by=template.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: TemplateModel) -> Template:
        return Template(
            id=model.id,
            format_id=model.format_id,
            is_active=model.is_active,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
