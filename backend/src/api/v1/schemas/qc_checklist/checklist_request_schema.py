"""ChecklistRequest — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChecklistRequestCreate(BaseModel):
    request_number: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="Draft", max_length=50)
    status_format: str = Field(default="", max_length=255)
    is_last_stage: bool = Field(default=False)
    is_removed: bool = Field(default=False)
    approver_user_id: int | None = Field(default=None)
    format_id: int | None = Field(default=None)


class ChecklistRequestUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=50)
    request_number: str | None = Field(default=None, min_length=1, max_length=100)
    status_format: str | None = Field(default=None, max_length=255)
    is_last_stage: bool | None = Field(default=None)
    is_removed: bool | None = Field(default=None)
    approver_user_id: int | None = Field(default=None)
    format_id: int | None = Field(default=None)


class ChecklistRequestResponse(BaseModel):
    id: int
    status: str
    request_number: str
    status_format: str
    is_last_stage: bool
    is_removed: bool
    sequence_number: int
    approver_user_id: int | None
    format_id: int | None
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class ChecklistRequestListResponse(BaseModel):
    items: list[ChecklistRequestResponse]
    total: int
    skip: int
    limit: int
