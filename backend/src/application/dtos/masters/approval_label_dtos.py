from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class CreateApprovalLabelDTO:
    label: str; stage_id: int; role_ids: list[int] = field(default_factory=list); is_active: bool = True

@dataclass(frozen=True)
class UpdateApprovalLabelDTO:
    label: str | None = None; stage_id: int | None = None; role_ids: list[int] | None = None; is_active: bool | None = None

@dataclass(frozen=True)
class ApprovalLabelDTO:
    id: int; label: str; stage_id: int; role_ids: list[int]; is_active: bool
    created_by: str; created_date: datetime; modified_by: str; modified_date: datetime

@dataclass(frozen=True)
class ApprovalLabelListDTO:
    items: list[ApprovalLabelDTO]; total: int; skip: int; limit: int
