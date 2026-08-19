"""ChecklistStage — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateChecklistStageDTO:
    checklist_request_id: int
    user_id: int | None = None
    format_stage_mapping_id: int | None = None
    status: str = "Pending"
    performed_remark: str = ""
    approved_remark: str = ""
    is_self_verified: bool = False
    self_verification_details: str = ""
    is_approvable: bool = False
    is_last_stage: bool = False
    submit_remarks: str = ""
    self_approved_remark: str = ""


@dataclass(frozen=True)
class UpdateChecklistStageDTO:
    status: str | None = None
    user_id: int | None = None
    format_stage_mapping_id: int | None = None
    performed_remark: str | None = None
    approved_remark: str | None = None
    is_self_verified: bool | None = None
    self_verification_details: str | None = None
    is_approvable: bool | None = None
    is_last_stage: bool | None = None
    submit_remarks: str | None = None
    self_approved_remark: str | None = None


@dataclass(frozen=True)
class ChecklistStageDTO:
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


@dataclass(frozen=True)
class ChecklistStageListDTO:
    items: list[ChecklistStageDTO]
    total: int
    skip: int
    limit: int
