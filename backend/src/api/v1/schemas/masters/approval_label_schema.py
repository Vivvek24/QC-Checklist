from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ApprovalLabelCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    stage_id: int
    role_ids: list[int] = Field(default_factory=list)
    is_active: bool = True
    @field_validator("label")
    @classmethod
    def _t(cls, v: str) -> str: return v.strip()

class ApprovalLabelUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    stage_id: int | None = None
    role_ids: list[int] | None = None
    is_active: bool | None = None
    @field_validator("label")
    @classmethod
    def _t(cls, v: str | None) -> str | None: return v.strip() if v else v

class ApprovalLabelResponse(BaseModel):
    id: int; label: str; stage_id: int; role_ids: list[int]; is_active: bool
    created_by: str; created_date: datetime; modified_by: str; modified_date: datetime

class ApprovalLabelListResponse(BaseModel):
    items: list[ApprovalLabelResponse]; total: int; skip: int; limit: int
