from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class RemarkCreate(BaseModel):
    remark: str = Field(..., min_length=1, max_length=2000)
    role_ids: list[int] = Field(default_factory=list)
    is_active: bool = True
    @field_validator("remark")
    @classmethod
    def _t(cls, v: str) -> str: return v.strip()

class RemarkUpdate(BaseModel):
    remark: str | None = Field(default=None, min_length=1, max_length=2000)
    role_ids: list[int] | None = None
    is_active: bool | None = None
    @field_validator("remark")
    @classmethod
    def _t(cls, v: str | None) -> str | None: return v.strip() if v else v

class RemarkResponse(BaseModel):
    id: int; remark: str; role_ids: list[int]; is_active: bool
    created_by: str; created_date: datetime; modified_by: str; modified_date: datetime

class RemarkListResponse(BaseModel):
    items: list[RemarkResponse]; total: int; skip: int; limit: int
