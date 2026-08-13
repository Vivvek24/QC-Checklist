"""Stage Master — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateStageDTO:
    stage_name: str
    is_active: bool = True


@dataclass(frozen=True)
class UpdateStageDTO:
    stage_name: str | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class StageDTO:
    id: int
    stage_name: str
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class StageListDTO:
    items: list[StageDTO]
    total: int
    skip: int
    limit: int
