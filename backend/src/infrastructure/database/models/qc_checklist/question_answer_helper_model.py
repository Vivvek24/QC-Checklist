"""QuestionAnswerHelper — SQLAlchemy ORM model. Table: question_answer_helpers."""

from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class QuestionAnswerHelperModel(BaseModel):
    __tablename__ = "question_answer_helpers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    text_box_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
