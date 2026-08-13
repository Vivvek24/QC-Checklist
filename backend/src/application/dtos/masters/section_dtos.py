"""Section Master — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateSectionDTO:
    section_name: str
    format_stage_mapping_id: int | None = None
    is_active: bool = True


@dataclass(frozen=True)
class UpdateSectionDTO:
    section_name: str | None = None
    format_stage_mapping_id: int | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class SectionDTO:
    id: int
    section_name: str
    format_stage_mapping_id: int | None
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class SectionListDTO:
    items: list[SectionDTO]
    total: int
    skip: int
    limit: int
