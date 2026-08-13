"""Question Master — application DTOs."""
from dataclasses import dataclass, field
from datetime import datetime
from src.domain.enums.answer_type_enum import AnswerType
from src.domain.enums.master_type_enum import MasterType


@dataclass(frozen=True)
class CreateQuestionDTO:
    title: str
    answer_type: AnswerType
    has_text_box: bool = False
    has_multiple_text_box: bool = False
    has_sub_question: bool = False
    is_validation_required: bool = False
    has_response_option: bool = False
    allow_multiple_input: bool = False
    has_associated_master: bool = False
    is_calculated: bool = False
    is_active: bool = True
    validation_type_id: int | None = None
    parent_question_id: int | None = None
    master_type: MasterType | None = None
    sub_question_ids: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateQuestionDTO:
    title: str | None = None
    answer_type: AnswerType | None = None
    has_text_box: bool | None = None
    has_multiple_text_box: bool | None = None
    has_sub_question: bool | None = None
    is_validation_required: bool | None = None
    has_response_option: bool | None = None
    allow_multiple_input: bool | None = None
    has_associated_master: bool | None = None
    is_calculated: bool | None = None
    is_active: bool | None = None
    validation_type_id: int | None = None
    parent_question_id: int | None = None
    master_type: MasterType | None = None
    sub_question_ids: list[int] | None = None


@dataclass(frozen=True)
class QuestionDTO:
    id: int
    title: str
    answer_type: AnswerType
    has_text_box: bool
    has_multiple_text_box: bool
    has_sub_question: bool
    is_validation_required: bool
    has_response_option: bool
    allow_multiple_input: bool
    has_associated_master: bool
    is_calculated: bool
    is_active: bool
    validation_type_id: int | None
    parent_question_id: int | None
    master_type: MasterType | None
    sub_question_ids: list[int]
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class QuestionListDTO:
    items: list[QuestionDTO]
    total: int
    skip: int
    limit: int
