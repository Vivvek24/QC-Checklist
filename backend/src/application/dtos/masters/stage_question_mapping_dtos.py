"""StageQuestionMapping — application DTOs."""

from dataclasses import dataclass
from datetime import datetime

from src.domain.enums.custom_answer_enum import CustomAnswer


@dataclass(frozen=True)
class CreateStageQuestionMappingDTO:
    format_stage_mapping_id: int
    question_id: int
    serial_number: int = 0
    show_on_grid: bool = False
    aql_limit: str = ""
    is_declaration_question: bool = False
    is_editable: bool = True
    custom_answers: CustomAnswer | None = None
    sap_field_id: int | None = None
    section_id: int | None = None
    is_active: bool = True


@dataclass(frozen=True)
class UpdateStageQuestionMappingDTO:
    format_stage_mapping_id: int | None = None
    question_id: int | None = None
    serial_number: int | None = None
    show_on_grid: bool | None = None
    aql_limit: str | None = None
    is_declaration_question: bool | None = None
    is_editable: bool | None = None
    custom_answers: CustomAnswer | None = None
    sap_field_id: int | None = None
    section_id: int | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class StageQuestionMappingDTO:
    id: int
    format_stage_mapping_id: int
    question_id: int
    sap_field_id: int | None
    section_id: int | None
    serial_number: int
    show_on_grid: bool
    aql_limit: str
    is_declaration_question: bool
    is_editable: bool
    custom_answers: CustomAnswer | None
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class StageQuestionMappingListDTO:
    items: list[StageQuestionMappingDTO]
    total: int
    skip: int
    limit: int
