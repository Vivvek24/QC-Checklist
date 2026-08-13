"""StageQuestionMapping — application service."""

from src.application.dtos.masters.stage_question_mapping_dtos import (
    CreateStageQuestionMappingDTO,
    StageQuestionMappingDTO,
    StageQuestionMappingListDTO,
    UpdateStageQuestionMappingDTO,
)
from src.domain.entities.masters.stage_question_mapping import StageQuestionMapping
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.masters.stage_question_mapping_repository import IStageQuestionMappingRepository

ENTITY = "StageQuestionMapping"


class StageQuestionMappingService:
    def __init__(self, repo: IStageQuestionMappingRepository) -> None:
        self._repo = repo

    async def list_mappings(self, skip: int = 0, limit: int = 100, is_active: bool | None = None) -> StageQuestionMappingListDTO:
        items = await self._repo.list_all(skip=skip, limit=limit, is_active=is_active)
        total = await self._repo.count(is_active=is_active)
        return StageQuestionMappingListDTO(items=[self._to_dto(i) for i in items], total=total, skip=skip, limit=limit)

    async def list_by_format_stage_mapping(self, format_stage_mapping_id: int) -> list[StageQuestionMappingDTO]:
        items = await self._repo.list_by_format_stage_mapping(format_stage_mapping_id)
        return [self._to_dto(i) for i in items]

    async def get_mapping(self, mapping_id: int) -> StageQuestionMappingDTO:
        return self._to_dto(await self._require(mapping_id))

    async def create_mapping(self, dto: CreateStageQuestionMappingDTO, actor: User) -> StageQuestionMappingDTO:
        if await self._repo.exists_by_mapping_and_question(dto.format_stage_mapping_id, dto.question_id):
            raise DuplicateEntityError(ENTITY, "format_stage_mapping_id+question_id", f"{dto.format_stage_mapping_id}+{dto.question_id}")
        created = await self._repo.create(StageQuestionMapping(
            format_stage_mapping_id=dto.format_stage_mapping_id,
            question_id=dto.question_id,
            sap_field_id=dto.sap_field_id,
            section_id=dto.section_id,
            serial_number=dto.serial_number,
            show_on_grid=dto.show_on_grid,
            aql_limit=dto.aql_limit,
            is_declaration_question=dto.is_declaration_question,
            is_editable=dto.is_editable,
            custom_answers=dto.custom_answers,
            is_active=dto.is_active,
            created_by=actor.username,
            modified_by=actor.username,
        ))
        return self._to_dto(created)

    async def update_mapping(self, mapping_id: int, dto: UpdateStageQuestionMappingDTO, actor: User) -> StageQuestionMappingDTO:
        mapping = await self._require(mapping_id)
        fsm_id = dto.format_stage_mapping_id if dto.format_stage_mapping_id is not None else mapping.format_stage_mapping_id
        q_id = dto.question_id if dto.question_id is not None else mapping.question_id
        if fsm_id != mapping.format_stage_mapping_id or q_id != mapping.question_id:
            if await self._repo.exists_by_mapping_and_question(fsm_id, q_id, exclude_id=mapping_id):
                raise DuplicateEntityError(ENTITY, "format_stage_mapping_id+question_id", f"{fsm_id}+{q_id}")
        if dto.format_stage_mapping_id is not None:
            mapping.format_stage_mapping_id = dto.format_stage_mapping_id
        if dto.question_id is not None:
            mapping.question_id = dto.question_id
        if dto.sap_field_id is not None:
            mapping.sap_field_id = dto.sap_field_id
        if dto.section_id is not None:
            mapping.section_id = dto.section_id
        if dto.serial_number is not None:
            mapping.serial_number = dto.serial_number
        if dto.show_on_grid is not None:
            mapping.show_on_grid = dto.show_on_grid
        if dto.aql_limit is not None:
            mapping.aql_limit = dto.aql_limit
        if dto.is_declaration_question is not None:
            mapping.is_declaration_question = dto.is_declaration_question
        if dto.is_editable is not None:
            mapping.is_editable = dto.is_editable
        if dto.custom_answers is not None:
            mapping.custom_answers = dto.custom_answers
        if dto.is_active is not None:
            mapping.is_active = dto.is_active
        mapping.mark_modified(actor.username)
        return self._to_dto(await self._repo.update(mapping))

    async def delete_mapping(self, mapping_id: int) -> None:
        await self._require(mapping_id)
        await self._repo.delete(mapping_id)

    async def _require(self, mapping_id: int) -> StageQuestionMapping:
        m = await self._repo.get_by_id(mapping_id)
        if m is None:
            raise EntityNotFoundError(ENTITY, mapping_id)
        return m

    @staticmethod
    def _to_dto(m: StageQuestionMapping) -> StageQuestionMappingDTO:
        return StageQuestionMappingDTO(
            id=m.id,
            format_stage_mapping_id=m.format_stage_mapping_id,
            question_id=m.question_id,
            sap_field_id=m.sap_field_id,
            section_id=m.section_id,
            serial_number=m.serial_number,
            show_on_grid=m.show_on_grid,
            aql_limit=m.aql_limit,
            is_declaration_question=m.is_declaration_question,
            is_editable=m.is_editable,
            custom_answers=m.custom_answers,
            is_active=m.is_active,
            created_by=m.created_by,
            created_date=m.created_date,
            modified_by=m.modified_by,
            modified_date=m.modified_date,
        )
