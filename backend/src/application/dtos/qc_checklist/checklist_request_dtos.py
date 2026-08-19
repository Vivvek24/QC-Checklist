"""ChecklistRequest — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateChecklistRequestDTO:
    request_number: str
    status: str = "Draft"
    status_format: str = ""
    is_last_stage: bool = False
    is_removed: bool = False
    approver_user_id: int | None = None
    format_id: int | None = None


@dataclass(frozen=True)
class UpdateChecklistRequestDTO:
    status: str | None = None
    request_number: str | None = None
    status_format: str | None = None
    is_last_stage: bool | None = None
    is_removed: bool | None = None
    approver_user_id: int | None = None
    format_id: int | None = None


@dataclass(frozen=True)
class ChecklistRequestDTO:
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


@dataclass(frozen=True)
class ChecklistRequestListDTO:
    items: list[ChecklistRequestDTO]
    total: int
    skip: int
    limit: int
