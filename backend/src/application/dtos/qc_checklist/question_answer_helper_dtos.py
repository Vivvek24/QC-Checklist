"""QuestionAnswerHelper — application DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateQuestionAnswerHelperDTO:
    text_box_value: str = ""


@dataclass(frozen=True)
class UpdateQuestionAnswerHelperDTO:
    text_box_value: str | None = None


@dataclass(frozen=True)
class QuestionAnswerHelperDTO:
    id: int
    text_box_value: str
    created_by: str
    created_date: datetime
    modified_by: str
    modified_date: datetime


@dataclass(frozen=True)
class QuestionAnswerHelperListDTO:
    items: list[QuestionAnswerHelperDTO]
    total: int
    skip: int
    limit: int
