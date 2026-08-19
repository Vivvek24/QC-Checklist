"""QuestionAnswerHelper — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class QuestionAnswerHelperCreate(BaseModel):
    text_box_value: str = Field(default="")
    question_answer_id: int | None = Field(default=None, description="If provided, links the helper to this question answer")


class QuestionAnswerHelperUpdate(BaseModel):
    text_box_value: str | None = Field(default=None)


class QuestionAnswerHelperResponse(BaseModel):
    id: int
    text_box_value: str
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class QuestionAnswerHelperListResponse(BaseModel):
    items: list[QuestionAnswerHelperResponse]
    total: int
    skip: int
    limit: int
