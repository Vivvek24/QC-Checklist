"""Format Master — Pydantic request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.domain.enums.format_enums import FormatType


class FormatCreate(BaseModel):
    format_no: str = Field(..., min_length=1, max_length=100, description="Unique format number")
    format_title: str = Field(..., min_length=1, max_length=255)
    format_name: str = Field(..., min_length=1, max_length=255)
    unit_id: int = Field(..., description="Parent unit ID")
    format_type: FormatType
    has_declaration_question: bool = Field(default=False)
    is_active: bool = Field(default=True)

    @field_validator("format_no", "format_title", "format_name")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class FormatUpdate(BaseModel):
    format_no: str | None = Field(default=None, min_length=1, max_length=100)
    format_title: str | None = Field(default=None, min_length=1, max_length=255)
    format_name: str | None = Field(default=None, min_length=1, max_length=255)
    unit_id: int | None = Field(default=None)
    format_type: FormatType | None = Field(default=None)
    has_declaration_question: bool | None = Field(default=None)
    is_active: bool | None = Field(default=None)

    @field_validator("format_no", "format_title", "format_name")
    @classmethod
    def _trim(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class FormatResponse(BaseModel):
    id: int
    format_no: str
    format_title: str
    format_name: str
    unit_id: int
    format_type: FormatType
    has_declaration_question: bool
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class FormatListResponse(BaseModel):
    items: list[FormatResponse]
    total: int
    skip: int
    limit: int
