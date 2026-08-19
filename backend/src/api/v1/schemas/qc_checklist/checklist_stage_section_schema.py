"""ChecklistStageSection — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChecklistStageSectionCreate(BaseModel):
    checklist_stage_id: int = Field(..., gt=0)
    section_id: int = Field(..., gt=0)


class ChecklistStageSectionUpdate(BaseModel):
    checklist_stage_id: int | None = Field(default=None, gt=0)
    section_id: int | None = Field(default=None, gt=0)


class ChecklistStageSectionResponse(BaseModel):
    id: int
    checklist_stage_id: int
    section_id: int
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class ChecklistStageSectionListResponse(BaseModel):
    items: list[ChecklistStageSectionResponse]
    total: int
    skip: int
    limit: int
