"""Stage Master — Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class StageCreate(BaseModel):
    stage_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = Field(default=True)

    @field_validator("stage_name")
    @classmethod
    def _trim(cls, v: str) -> str:
        return v.strip()


class StageUpdate(BaseModel):
    stage_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = Field(default=None)

    @field_validator("stage_name")
    @classmethod
    def _trim(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class StageResponse(BaseModel):
    id: int
    stage_name: str
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class StageListResponse(BaseModel):
    items: list[StageResponse]
    total: int
    skip: int
    limit: int
