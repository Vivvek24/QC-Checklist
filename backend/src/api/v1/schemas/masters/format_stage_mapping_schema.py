"""FormatStageMapping — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class FormatStageMappingCreate(BaseModel):
    format_id: int = Field(..., gt=0)
    stage_id: int = Field(..., gt=0)
    is_active: bool = Field(default=True)
    is_approvable: bool = Field(default=False)
    is_refer_back: bool = Field(default=False)
    has_section: bool = Field(default=False)


class FormatStageMappingUpdate(BaseModel):
    format_id: int | None = Field(default=None, gt=0)
    stage_id: int | None = Field(default=None, gt=0)
    is_active: bool | None = Field(default=None)
    is_approvable: bool | None = Field(default=None)
    is_refer_back: bool | None = Field(default=None)
    has_section: bool | None = Field(default=None)


class FormatStageMappingResponse(BaseModel):
    id: int
    format_id: int
    stage_id: int
    is_active: bool
    is_approvable: bool
    is_refer_back: bool
    has_section: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class FormatStageMappingListResponse(BaseModel):
    items: list[FormatStageMappingResponse]
    total: int
    skip: int
    limit: int
