"""Template — Pydantic request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.enums.template_enums import ColumnType


class TemplateResponse(BaseModel):
    id: int
    format_id: int
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class TemplateColumnInput(BaseModel):
    header: str = Field(default="", max_length=255)
    column_type: ColumnType
    width: str | None = Field(default=None, max_length=30)
    is_required: bool = Field(default=False)


class ReplaceColumnsForScopeRequest(BaseModel):
    format_id: int = Field(..., ge=1)
    format_stage_mapping_id: int = Field(..., ge=1)
    section_id: int | None = Field(default=None)
    columns: list[TemplateColumnInput] = Field(default_factory=list)


class TemplateColumnResponse(BaseModel):
    id: int
    template_id: int
    format_stage_mapping_id: int
    section_id: int | None
    header: str
    column_type: ColumnType
    display_order: int
    width: str | None
    is_required: bool


class TemplateColumnListResponse(BaseModel):
    items: list[TemplateColumnResponse]
