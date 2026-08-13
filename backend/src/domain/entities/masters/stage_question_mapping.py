"""StageQuestionMapping — domain entity."""

from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity
from src.domain.enums.custom_answer_enum import CustomAnswer


@dataclass
class StageQuestionMapping(BaseEntity):
    """Maps a Question to a FormatStageMapping with display/behaviour config."""

    format_stage_mapping_id: int = field(default=0)
    question_id: int = field(default=0)
    sap_field_id: int | None = field(default=None)
    section_id: int | None = field(default=None)
    serial_number: int = field(default=0)
    show_on_grid: bool = field(default=False)
    aql_limit: str = field(default="")
    is_declaration_question: bool = field(default=False)
    is_editable: bool = field(default=True)
    custom_answers: CustomAnswer | None = field(default=None)
    is_active: bool = field(default=True)
