"""StageQuestionMapping — repository implementation."""

from typing import Any

from sqlalchemy import ColumnElement, Select, func, select

from src.domain.entities.masters.stage_question_mapping import StageQuestionMapping
from src.domain.enums.custom_answer_enum import CustomAnswer
from src.domain.repositories.masters.stage_question_mapping_repository import IStageQuestionMappingRepository
from src.infrastructure.database.models.masters.stage_question_mapping_model import StageQuestionMappingModel
from src.infrastructure.database.repositories.base_repository_impl import SqlAlchemyRepository


class StageQuestionMappingRepositoryImpl(SqlAlchemyRepository[StageQuestionMapping, StageQuestionMappingModel], IStageQuestionMappingRepository):
    _model = StageQuestionMappingModel

    @staticmethod
    def _code_equals(code: str) -> ColumnElement[bool]:
        return StageQuestionMappingModel.id == -1

    async def list_all(self, skip: int = 0, limit: int = 100, search: str | None = None, is_active: bool | None = None) -> list[StageQuestionMapping]:
        stmt = self._apply_filters(select(StageQuestionMappingModel), search, is_active)
        stmt = stmt.order_by(StageQuestionMappingModel.serial_number).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, search: str | None = None, is_active: bool | None = None) -> int:
        stmt = self._apply_filters(select(func.count()).select_from(StageQuestionMappingModel), search, is_active)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_by_format_stage_mapping(self, format_stage_mapping_id: int) -> list[StageQuestionMapping]:
        stmt = select(StageQuestionMappingModel).where(
            StageQuestionMappingModel.format_stage_mapping_id == format_stage_mapping_id
        ).order_by(StageQuestionMappingModel.serial_number)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def exists_by_code(self, code: str, exclude_id: int | None = None) -> bool:
        return False

    async def exists_by_mapping_and_question(
        self, format_stage_mapping_id: int, question_id: int, exclude_id: int | None = None
    ) -> bool:
        stmt = select(StageQuestionMappingModel.id).where(
            StageQuestionMappingModel.format_stage_mapping_id == format_stage_mapping_id,
            StageQuestionMappingModel.question_id == question_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(StageQuestionMappingModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, entity: StageQuestionMapping) -> StageQuestionMapping:
        model = StageQuestionMappingModel(
            format_stage_mapping_id=entity.format_stage_mapping_id,
            question_id=entity.question_id,
            sap_field_id=entity.sap_field_id,
            section_id=entity.section_id,
            serial_number=entity.serial_number,
            show_on_grid=entity.show_on_grid,
            aql_limit=entity.aql_limit,
            is_declaration_question=entity.is_declaration_question,
            is_editable=entity.is_editable,
            custom_answers=entity.custom_answers.value if entity.custom_answers else None,
            is_active=entity.is_active,
            created_by=entity.created_by,
            modified_by=entity.modified_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: StageQuestionMapping) -> StageQuestionMapping:
        model = await self._require_model(entity.id)
        model.format_stage_mapping_id = entity.format_stage_mapping_id
        model.question_id = entity.question_id
        model.sap_field_id = entity.sap_field_id
        model.section_id = entity.section_id
        model.serial_number = entity.serial_number
        model.show_on_grid = entity.show_on_grid
        model.aql_limit = entity.aql_limit
        model.is_declaration_question = entity.is_declaration_question
        model.is_editable = entity.is_editable
        model.custom_answers = entity.custom_answers.value if entity.custom_answers else None
        model.is_active = entity.is_active
        model.modified_by = entity.modified_by
        model.modified_date = entity.modified_date
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _apply_filters(stmt: Select[Any], search: str | None, is_active: bool | None) -> Select[Any]:
        if is_active is not None:
            stmt = stmt.where(StageQuestionMappingModel.is_active.is_(is_active))
        return stmt

    @staticmethod
    def _to_entity(model: StageQuestionMappingModel) -> StageQuestionMapping:
        return StageQuestionMapping(
            id=model.id,
            format_stage_mapping_id=model.format_stage_mapping_id,
            question_id=model.question_id,
            sap_field_id=model.sap_field_id,
            section_id=model.section_id,
            serial_number=model.serial_number,
            show_on_grid=model.show_on_grid,
            aql_limit=model.aql_limit,
            is_declaration_question=model.is_declaration_question,
            is_editable=model.is_editable,
            custom_answers=CustomAnswer(model.custom_answers) if model.custom_answers else None,
            is_active=model.is_active,
            created_by=model.created_by,
            created_date=model.created_date,
            modified_by=model.modified_by,
            modified_date=model.modified_date,
        )
