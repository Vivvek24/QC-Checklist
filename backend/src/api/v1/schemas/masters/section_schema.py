"""Section Master — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SectionCreate(BaseModel):
    section_name: str = Field(..., min_length=1, max_length=255)
    format_stage_mapping_id: int | None = Field(default=None)
    is_active: bool = Field(default=True)

    @field_validator("section_name")
    @classmethod
    def _trim(cls, v: str) -> str:
        return v.strip()


class SectionUpdate(BaseModel):
    section_name: str | None = Field(default=None, min_length=1, max_length=255)
    format_stage_mapping_id: int | None = Field(default=None)
    is_active: bool | None = Field(default=None)

    @field_validator("section_name")
    @classmethod
    def _trim(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class SectionResponse(BaseModel):
    id: int
    section_name: str
    format_stage_mapping_id: int | None
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class SectionListResponse(BaseModel):
    items: list[SectionResponse]
    total: int
    skip: int
    limit: int
