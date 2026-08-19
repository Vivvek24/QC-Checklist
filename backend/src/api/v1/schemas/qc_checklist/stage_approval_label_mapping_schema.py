"""StageApprovalLabelMapping — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class StageApprovalLabelMappingCreate(BaseModel):
    checklist_stage_id: int = Field(..., gt=0)
    approval_label_id: int = Field(..., gt=0)
    remark_id: int | None = Field(default=None)
    user_id: int | None = Field(default=None)
    role_id: int | None = Field(default=None)
    date_of_action: datetime | None = Field(default=None)
    remark: str = Field(default="")
    is_show: bool = Field(default=False)
    is_refer_back: bool = Field(default=False)


class StageApprovalLabelMappingUpdate(BaseModel):
    approval_label_id: int | None = Field(default=None, gt=0)
    remark_id: int | None = Field(default=None)
    user_id: int | None = Field(default=None)
    role_id: int | None = Field(default=None)
    date_of_action: datetime | None = Field(default=None)
    remark: str | None = Field(default=None)
    is_show: bool | None = Field(default=None)
    is_refer_back: bool | None = Field(default=None)


class StageApprovalLabelMappingResponse(BaseModel):
    id: int
    checklist_stage_id: int
    approval_label_id: int
    remark_id: int | None
    user_id: int | None
    role_id: int | None
    date_of_action: datetime | None
    remark: str
    is_show: bool
    is_refer_back: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class StageApprovalLabelMappingListResponse(BaseModel):
    items: list[StageApprovalLabelMappingResponse]
    total: int
    skip: int
    limit: int
