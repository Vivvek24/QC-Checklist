"""StageApprovalLabelMapping — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateStageApprovalLabelMappingDTO:
    checklist_stage_id: int
    approval_label_id: int
    remark_id: int | None = None
    user_id: int | None = None
    role_id: int | None = None
    date_of_action: datetime | None = None
    remark: str = ""
    is_show: bool = False
    is_refer_back: bool = False


@dataclass(frozen=True)
class UpdateStageApprovalLabelMappingDTO:
    approval_label_id: int | None = None
    remark_id: int | None = None
    user_id: int | None = None
    role_id: int | None = None
    date_of_action: datetime | None = None
    remark: str | None = None
    is_show: bool | None = None
    is_refer_back: bool | None = None


@dataclass(frozen=True)
class StageApprovalLabelMappingDTO:
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


@dataclass(frozen=True)
class StageApprovalLabelMappingListDTO:
    items: list[StageApprovalLabelMappingDTO]
    total: int
    skip: int
    limit: int
