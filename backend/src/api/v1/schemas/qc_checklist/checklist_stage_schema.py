"""ChecklistStage — Pydantic schemas."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ChecklistStageStatusEnum(StrEnum):
    PENDING = "Pending"
    APPROVED = "Approved"
    DRAFT = "Draft"
    REFER_BACK = "ReferBack"
    INITIAL = "Initial"
    REMOVED = "Removed"
    SAVED = "Saved"


class ChecklistStageCreate(BaseModel):
    checklist_request_id: int = Field(..., gt=0)
    user_id: int | None = Field(default=None)
    format_stage_mapping_id: int | None = Field(default=None)
    status: ChecklistStageStatusEnum = Field(default=ChecklistStageStatusEnum.PENDING)
    performed_remark: str = Field(default="")
    approved_remark: str = Field(default="")
    is_self_verified: bool = Field(default=False)
    self_verification_details: str = Field(default="")
    is_approvable: bool = Field(default=False)
    is_last_stage: bool = Field(default=False)
    submit_remarks: str = Field(default="")
    self_approved_remark: str = Field(default="")


class ChecklistStageUpdate(BaseModel):
    status: ChecklistStageStatusEnum | None = Field(default=None)
    user_id: int | None = Field(default=None)
    format_stage_mapping_id: int | None = Field(default=None)
    performed_remark: str | None = Field(default=None)
    approved_remark: str | None = Field(default=None)
    is_self_verified: bool | None = Field(default=None)
    self_verification_details: str | None = Field(default=None)
    is_approvable: bool | None = Field(default=None)
    is_last_stage: bool | None = Field(default=None)
    submit_remarks: str | None = Field(default=None)
    self_approved_remark: str | None = Field(default=None)


class ChecklistStageResponse(BaseModel):
    id: int
    checklist_request_id: int
    user_id: int | None
    format_stage_mapping_id: int | None
    status: str
    performed_remark: str
    approved_remark: str
    is_self_verified: bool
    self_verification_details: str
    is_approvable: bool
    is_last_stage: bool
    submit_remarks: str
    self_approved_remark: str
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class ChecklistStageListResponse(BaseModel):
    items: list[ChecklistStageResponse]
    total: int
    skip: int
    limit: int
