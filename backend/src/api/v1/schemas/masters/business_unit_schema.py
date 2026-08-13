"""
Business Unit Master — Pydantic request/response schemas (HTTP contract).
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class BusinessUnitCreate(BaseModel):
    """Request body: create a business unit."""

    name: str = Field(..., min_length=1, max_length=255, description="Business unit name")
    is_active: bool = Field(default=True, description="Active status")

    @field_validator("name")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()


class BusinessUnitUpdate(BaseModel):
    """Request body: partial update of a business unit."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def _trim(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class BusinessUnitResponse(BaseModel):
    """Response schema for a single business unit."""

    id: int
    name: str
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class BusinessUnitListResponse(BaseModel):
    """Paginated list of business units."""

    items: list[BusinessUnitResponse]
    total: int
    skip: int
    limit: int
