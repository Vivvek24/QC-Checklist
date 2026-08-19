"""QuestionAnswer — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateQuestionAnswerDTO:
    checklist_stage_id: int
    checklist_stage_section_id: int | None = None
    product_id: int | None = None
    question_id: int | None = None
    question_option_id: int | None = None
    receiver_user_id: int | None = None
    response_question_option_id: int | None = None
    stage_question_mapping_id: int | None = None
    textbox_value: str = ""
    response_answer: str = ""
    comma_separated_name: str = ""
    has_helper: bool = False
    serial_number: int = 0
    sub_answer_serial_no: str = ""
    date_time: datetime | None = None
    test_title: str = ""
    sample_vails: str = ""
    answer_total_vails: int = 0
    issued_by_date: datetime | None = None
    received_by_date: datetime | None = None
    issuer_name: str = ""
    is_issued_vails: bool = False
    has_vails: bool = False


@dataclass(frozen=True)
class UpdateQuestionAnswerDTO:
    checklist_stage_section_id: int | None = None
    product_id: int | None = None
    question_id: int | None = None
    question_option_id: int | None = None
    receiver_user_id: int | None = None
    response_question_option_id: int | None = None
    stage_question_mapping_id: int | None = None
    textbox_value: str | None = None
    response_answer: str | None = None
    comma_separated_name: str | None = None
    has_helper: bool | None = None
    serial_number: int | None = None
    sub_answer_serial_no: str | None = None
    date_time: datetime | None = None
    test_title: str | None = None
    sample_vails: str | None = None
    answer_total_vails: int | None = None
    issued_by_date: datetime | None = None
    received_by_date: datetime | None = None
    issuer_name: str | None = None
    is_issued_vails: bool | None = None
    has_vails: bool | None = None


@dataclass(frozen=True)
class QuestionAnswerDTO:
    id: int
    checklist_stage_id: int
    checklist_stage_section_id: int | None
    product_id: int | None
    question_id: int | None
    question_option_id: int | None
    receiver_user_id: int | None
    response_question_option_id: int | None
    stage_question_mapping_id: int | None
    textbox_value: str
    response_answer: str
    comma_separated_name: str
    has_helper: bool
    serial_number: int
    sub_answer_serial_no: str
    date_time: datetime | None
    test_title: str
    sample_vails: str
    answer_total_vails: int
    issued_by_date: datetime | None
    received_by_date: datetime | None
    issuer_name: str
    is_issued_vails: bool
    has_vails: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class QuestionAnswerListDTO:
    items: list[QuestionAnswerDTO]
    total: int
    skip: int
    limit: int
