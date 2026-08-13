"""TestMaster — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TestMasterCreate(BaseModel):
    test_name: str = Field(..., min_length=1, max_length=255)
    no_of_samples_issued: int = Field(default=0, ge=0)
    sample_qty: int = Field(default=0, ge=0)
    product_id: int = Field(..., gt=0)
    is_active: bool = Field(default=True)

    @field_validator("test_name")
    @classmethod
    def _trim(cls, v: str) -> str:
        return v.strip()


class TestMasterUpdate(BaseModel):
    test_name: str | None = Field(default=None, min_length=1, max_length=255)
    no_of_samples_issued: int | None = Field(default=None, ge=0)
    sample_qty: int | None = Field(default=None, ge=0)
    product_id: int | None = Field(default=None, gt=0)
    is_active: bool | None = Field(default=None)

    @field_validator("test_name")
    @classmethod
    def _trim(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class TestMasterResponse(BaseModel):
    id: int
    test_name: str
    no_of_samples_issued: int
    sample_qty: int
    product_id: int
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class TestMasterListResponse(BaseModel):
    items: list[TestMasterResponse]
    total: int
    skip: int
    limit: int
