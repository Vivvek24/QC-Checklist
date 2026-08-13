"""Product Master — Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ProductCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255)
    storage_conditions: str = Field(default="", max_length=2000)
    is_active: bool = True
    @field_validator("product_name", "storage_conditions")
    @classmethod
    def _trim(cls, v: str) -> str: return v.strip()

class ProductUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    storage_conditions: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None
    @field_validator("product_name", "storage_conditions")
    @classmethod
    def _trim(cls, v: str | None) -> str | None: return v.strip() if v else v

class ProductResponse(BaseModel):
    id: int; product_name: str; storage_conditions: str; is_active: bool
    created_by: str; created_date: datetime; modified_by: str; modified_date: datetime

class ProductListResponse(BaseModel):
    items: list[ProductResponse]; total: int; skip: int; limit: int
