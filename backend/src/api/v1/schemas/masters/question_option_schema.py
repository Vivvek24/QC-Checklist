"""QuestionOption Master — Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class QuestionOptionCreate(BaseModel):
    option_title: str = Field(..., min_length=1, max_length=500)
    is_response_option: bool = Field(default=False)
    question_id: int = Field(..., gt=0)
    is_active: bool = Field(default=True)

    @field_validator("option_title")
    @classmethod
    def _trim(cls, v: str) -> str:
        return v.strip()


class QuestionOptionUpdate(BaseModel):
    option_title: str | None = Field(default=None, min_length=1, max_length=500)
    is_response_option: bool | None = Field(default=None)
    question_id: int | None = Field(default=None, gt=0)
    is_active: bool | None = Field(default=None)

    @field_validator("option_title")
    @classmethod
    def _trim(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class QuestionOptionResponse(BaseModel):
    id: int
    option_title: str
    is_response_option: bool
    question_id: int
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


class QuestionOptionListResponse(BaseModel):
    items: list[QuestionOptionResponse]
    total: int
    skip: int
    limit: int
