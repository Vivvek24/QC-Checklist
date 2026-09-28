"""Template — application DTOs."""

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.enums.template_enums import ColumnType


@dataclass(frozen=True)
class TemplateDTO:
    id: int
    format_id: int
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class ColumnInputDTO:
    header: str
    column_type: ColumnType
    display_order: int
    width: str | None = None
    is_required: bool = False


@dataclass(frozen=True)
class ReplaceColumnsForScopeDTO:
    format_id: int
    format_stage_mapping_id: int
    section_id: int | None
    columns: list[ColumnInputDTO] = field(default_factory=list)


@dataclass(frozen=True)
class TemplateLayoutColumnDTO:
    id: int
    template_id: int
    format_stage_mapping_id: int
    section_id: int | None
    header: str
    column_type: ColumnType
    display_order: int
    width: str | None
    is_required: bool
