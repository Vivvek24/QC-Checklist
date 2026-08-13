"""Unit Master — Pydantic request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UnitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    business_unit_id: int = Field(..., description="Parent business unit ID")
    is_active: bool = Field(default=True)

    @field_validator("name")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class UnitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    business_unit_id: int | None = Field(default=None)
    is_active: bool | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def _trim(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class UnitResponse(BaseModel):
    id: int
    name: str
    business_unit_id: int
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class UnitListResponse(BaseModel):
    items: list[UnitResponse]
    total: int
    skip: int
    limit: int
