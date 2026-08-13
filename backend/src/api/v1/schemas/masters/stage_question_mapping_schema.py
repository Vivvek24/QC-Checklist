"""StageQuestionMapping — Pydantic schemas."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class CustomAnswerEnum(StrEnum):
    START_DATE = "StartDate"
    END_DATE = "EndDate"
    CALCULATE_SAMPLE_DESTROYED = "Calculate_SampleDestroyed"
    CALCULATE_SAMPLE_CONSUMED = "Calculate_SampleConsumed"


class StageQuestionMappingCreate(BaseModel):
    format_stage_mapping_id: int = Field(..., gt=0)
    question_id: int = Field(..., gt=0)
    sap_field_id: int | None = Field(default=None)
    section_id: int | None = Field(default=None)
    serial_number: int = Field(default=0, ge=0)
    show_on_grid: bool = Field(default=False)
    aql_limit: str = Field(default="", max_length=100)
    is_declaration_question: bool = Field(default=False)
    is_editable: bool = Field(default=True)
    custom_answers: CustomAnswerEnum | None = Field(default=None)
    is_active: bool = Field(default=True)


class StageQuestionMappingUpdate(BaseModel):
    format_stage_mapping_id: int | None = Field(default=None, gt=0)
    question_id: int | None = Field(default=None, gt=0)
    sap_field_id: int | None = Field(default=None)
    section_id: int | None = Field(default=None)
    serial_number: int | None = Field(default=None, ge=0)
    show_on_grid: bool | None = Field(default=None)
    aql_limit: str | None = Field(default=None, max_length=100)
    is_declaration_question: bool | None = Field(default=None)
    is_editable: bool | None = Field(default=None)
    custom_answers: CustomAnswerEnum | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class StageQuestionMappingResponse(BaseModel):
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
    custom_answers: CustomAnswerEnum | None
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class StageQuestionMappingListResponse(BaseModel):
    items: list[StageQuestionMappingResponse]
    total: int
    skip: int
    limit: int
