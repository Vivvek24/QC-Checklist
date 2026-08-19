"""ChecklistStageSection — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateChecklistStageSectionDTO:
    checklist_stage_id: int
    section_id: int


@dataclass(frozen=True)
class UpdateChecklistStageSectionDTO:
    checklist_stage_id: int | None = None
    section_id: int | None = None


@dataclass(frozen=True)
class ChecklistStageSectionDTO:
    id: int
    checklist_stage_id: int
    section_id: int
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class ChecklistStageSectionListDTO:
    items: list[ChecklistStageSectionDTO]
    total: int
    skip: int
    limit: int
