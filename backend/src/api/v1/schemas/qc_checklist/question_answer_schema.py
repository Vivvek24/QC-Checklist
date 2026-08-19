"""QuestionAnswer — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class QuestionAnswerCreate(BaseModel):
    checklist_stage_id: int = Field(..., gt=0)
    checklist_stage_section_id: int | None = Field(default=None)
    product_id: int | None = Field(default=None)
    question_id: int | None = Field(default=None)
    question_option_id: int | None = Field(default=None)
    receiver_user_id: int | None = Field(default=None)
    response_question_option_id: int | None = Field(default=None)
    stage_question_mapping_id: int | None = Field(default=None)
    textbox_value: str = Field(default="")
    response_answer: str = Field(default="", max_length=100)
    comma_separated_name: str = Field(default="")
    has_helper: bool = Field(default=False)
    serial_number: int = Field(default=0)
    sub_answer_serial_no: str = Field(default="", max_length=100)
    date_time: datetime | None = Field(default=None)
    test_title: str = Field(default="", max_length=255)
    sample_vails: str = Field(default="", max_length=255)
    answer_total_vails: int = Field(default=0)
    issued_by_date: datetime | None = Field(default=None)
    received_by_date: datetime | None = Field(default=None)
    issuer_name: str = Field(default="", max_length=255)
    is_issued_vails: bool = Field(default=False)
    has_vails: bool = Field(default=False)


class QuestionAnswerUpdate(BaseModel):
    checklist_stage_section_id: int | None = Field(default=None)
    product_id: int | None = Field(default=None)
    question_id: int | None = Field(default=None)
    question_option_id: int | None = Field(default=None)
    receiver_user_id: int | None = Field(default=None)
    response_question_option_id: int | None = Field(default=None)
    stage_question_mapping_id: int | None = Field(default=None)
    textbox_value: str | None = Field(default=None)
    response_answer: str | None = Field(default=None, max_length=100)
    comma_separated_name: str | None = Field(default=None)
    has_helper: bool | None = Field(default=None)
    serial_number: int | None = Field(default=None)
    sub_answer_serial_no: str | None = Field(default=None, max_length=100)
    date_time: datetime | None = Field(default=None)
    test_title: str | None = Field(default=None, max_length=255)
    sample_vails: str | None = Field(default=None, max_length=255)
    answer_total_vails: int | None = Field(default=None)
    issued_by_date: datetime | None = Field(default=None)
    received_by_date: datetime | None = Field(default=None)
    issuer_name: str | None = Field(default=None, max_length=255)
    is_issued_vails: bool | None = Field(default=None)
    has_vails: bool | None = Field(default=None)


class QuestionAnswerResponse(BaseModel):
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


class QuestionAnswerListResponse(BaseModel):
    items: list[QuestionAnswerResponse]
    total: int
    skip: int
    limit: int
