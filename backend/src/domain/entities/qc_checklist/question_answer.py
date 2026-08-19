"""QuestionAnswer — domain entity."""

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.entities.base_entity import BaseEntity


@dataclass
class QuestionAnswer(BaseEntity):
    """An answer to a question within a checklist stage."""

    checklist_stage_id: int = field(default=0)
    checklist_stage_section_id: int | None = field(default=None)
    product_id: int | None = field(default=None)
    question_id: int | None = field(default=None)
    question_option_id: int | None = field(default=None)
    receiver_user_id: int | None = field(default=None)
    response_question_option_id: int | None = field(default=None)
    stage_question_mapping_id: int | None = field(default=None)
    textbox_value: str = field(default="")
    response_answer: str = field(default="")
    comma_separated_name: str = field(default="")
    has_helper: bool = field(default=False)
    serial_number: int = field(default=0)
    sub_answer_serial_no: str = field(default="")
    date_time: datetime | None = field(default=None)
    test_title: str = field(default="")
    sample_vails: str = field(default="")
    answer_total_vails: int = field(default=0)
    issued_by_date: datetime | None = field(default=None)
    received_by_date: datetime | None = field(default=None)
    issuer_name: str = field(default="")
    is_issued_vails: bool = field(default=False)
    has_vails: bool = field(default=False)
