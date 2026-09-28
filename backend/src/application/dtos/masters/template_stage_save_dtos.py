"""Template Stage Save — application DTOs.

One request atomically replaces everything Template Studio owns for a single
stage: its own rows + columns, and each of its nested sections' rows +
columns, plus any rows/sections removed from the canvas since the last save.
"""

from dataclasses import dataclass, field

from src.domain.enums.custom_answer_enum import CustomAnswer
from src.domain.enums.template_enums import ColumnType


@dataclass(frozen=True)
class StageSaveColumnDTO:
    header: str
    column_type: ColumnType
    width: str | None = None
    is_required: bool = False


@dataclass(frozen=True)
class StageSaveRowDTO:
    """A single stage_question_mappings row. `mapping_id` set = update, unset = create."""

    question_id: int
    mapping_id: int | None = None
    show_on_grid: bool = False
    sap_field_id: int | None = None
    is_editable: bool = True
    is_declaration_question: bool = False
    custom_answers: CustomAnswer | None = None
    aql_limit: str = ""
    is_active: bool = True


@dataclass(frozen=True)
class StageSaveSectionDTO:
    """A single section and its own rows/columns. `section_id` set = update, unset = create."""

    section_name: str
    section_id: int | None = None
    rows: list[StageSaveRowDTO] = field(default_factory=list)
    columns: list[StageSaveColumnDTO] = field(default_factory=list)


@dataclass(frozen=True)
class TemplateStageSaveDTO:
    format_id: int
    stage_id: int
    rows: list[StageSaveRowDTO] = field(default_factory=list)
    columns: list[StageSaveColumnDTO] = field(default_factory=list)
    sections: list[StageSaveSectionDTO] = field(default_factory=list)
    deleted_mapping_ids: list[int] = field(default_factory=list)
    deleted_section_ids: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class StageSaveRowResultDTO:
    id: int
    question_id: int
    serial_number: int


@dataclass(frozen=True)
class StageSaveSectionResultDTO:
    id: int
    section_name: str
    rows: list[StageSaveRowResultDTO] = field(default_factory=list)


@dataclass(frozen=True)
class TemplateStageSaveResultDTO:
    format_stage_mapping_id: int
    rows: list[StageSaveRowResultDTO] = field(default_factory=list)
    sections: list[StageSaveSectionResultDTO] = field(default_factory=list)
