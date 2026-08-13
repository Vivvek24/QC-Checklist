"""Question Master — domain entity."""
from dataclasses import dataclass, field

from src.domain.entities.base_entity import BaseEntity
from src.domain.enums.answer_type_enum import AnswerType
from src.domain.enums.master_type_enum import MasterType


@dataclass
class Question(BaseEntity):
    title: str = field(default="")
    answer_type: AnswerType = field(default=AnswerType.NONE)
    has_text_box: bool = field(default=False)
    has_multiple_text_box: bool = field(default=False)
    has_sub_question: bool = field(default=False)
    is_validation_required: bool = field(default=False)
    has_response_option: bool = field(default=False)
    allow_multiple_input: bool = field(default=False)
    has_associated_master: bool = field(default=False)
    is_calculated: bool = field(default=False)
    is_active: bool = field(default=True)
    validation_type_id: int | None = field(default=None)
    parent_question_id: int | None = field(default=None)
    master_type: MasterType | None = field(default=None)
    sub_question_ids: list[int] = field(default_factory=list)
