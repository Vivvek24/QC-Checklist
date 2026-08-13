from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class CreateRemarkDTO:
    remark: str
    role_ids: list[int] = field(default_factory=list)
    is_active: bool = True

@dataclass(frozen=True)
class UpdateRemarkDTO:
    remark: str | None = None
    role_ids: list[int] | None = None
    is_active: bool | None = None

@dataclass(frozen=True)
class RemarkDTO:
    id: int
    remark: str
    role_ids: list[int]
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime

@dataclass(frozen=True)
class RemarkListDTO:
    items: list[RemarkDTO]
    total: int
    skip: int
    limit: int
