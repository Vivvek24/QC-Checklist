"""Format Master — application DTOs."""

from dataclasses import dataclass
from datetime import datetime

from src.domain.enums.format_enums import FormatType


@dataclass(frozen=True)
class CreateFormatDTO:
    format_no: str
    format_title: str
    format_name: str
    unit_id: int
    format_type: FormatType
    has_declaration_question: bool = False
    is_active: bool = True


@dataclass(frozen=True)
class UpdateFormatDTO:
    format_no: str | None = None
    format_title: str | None = None
    format_name: str | None = None
    unit_id: int | None = None
    format_type: FormatType | None = None
    has_declaration_question: bool | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class FormatDTO:
    id: int
    format_no: str
    format_title: str
    format_name: str
    unit_id: int
    format_type: FormatType
    has_declaration_question: bool
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class FormatListDTO:
    items: list[FormatDTO]
    total: int
    skip: int
    limit: int
