"""QuestionOption Master — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateQuestionOptionDTO:
    option_title: str
    is_response_option: bool
    question_id: int
    is_active: bool = True


@dataclass(frozen=True)
class UpdateQuestionOptionDTO:
    option_title: str | None = None
    is_response_option: bool | None = None
    question_id: int | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class QuestionOptionDTO:
    id: int
    option_title: str
    is_response_option: bool
    question_id: int
    is_active: bool
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class QuestionOptionListDTO:
    items: list[QuestionOptionDTO]
    total: int
    skip: int
    limit: int
