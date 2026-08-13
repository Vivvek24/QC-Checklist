from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class SapFieldCreate(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    @field_validator("field_name")
    @classmethod
    def _t(cls, v: str) -> str: return v.strip()

class SapFieldUpdate(BaseModel):
    field_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None
    @field_validator("field_name")
    @classmethod
    def _t(cls, v: str | None) -> str | None: return v.strip() if v else v

class SapFieldResponse(BaseModel):
    id: int; field_name: str; is_active: bool; created_by: str; created_date: datetime; modified_by: str; modified_date: datetime

class SapFieldListResponse(BaseModel):
    items: list[SapFieldResponse]; total: int; skip: int; limit: int
