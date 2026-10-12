"""QuestionAnswerHelper — SQLAlchemy ORM model. Table: question_answer_helpers.

A helper ("+ Add") value that belongs to a QuestionAnswer. The question_answer_id
FK ties each helper to its owning answer.
"""

from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class QuestionAnswerHelperModel(BaseModel):
    __tablename__ = "question_answer_helpers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    question_answer_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("question_answers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    text_box_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
