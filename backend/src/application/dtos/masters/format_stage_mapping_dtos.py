"""FormatStageMapping — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateFormatStageMappingDTO:
    format_id: int
    stage_id: int
    is_active: bool = True
    is_approvable: bool = False
    is_refer_back: bool = False
    has_section: bool = False


@dataclass(frozen=True)
class UpdateFormatStageMappingDTO:
    format_id: int | None = None
    stage_id: int | None = None
    is_active: bool | None = None
    is_approvable: bool | None = None
    is_refer_back: bool | None = None
    has_section: bool | None = None


@dataclass(frozen=True)
class FormatStageMappingDTO:
    id: int
    format_id: int
    stage_id: int
    is_active: bool
    is_approvable: bool
    is_refer_back: bool
    has_section: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class FormatStageMappingListDTO:
    items: list[FormatStageMappingDTO]
    total: int
    skip: int
    limit: int
