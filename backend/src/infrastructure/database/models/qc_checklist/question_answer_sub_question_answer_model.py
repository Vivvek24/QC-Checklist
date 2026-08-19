"""QuestionAnswer_SubQuestionAnswer — junction table for many-to-many between QuestionAnswer and QuestionAnswerHelper."""

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class QuestionAnswerSubQuestionAnswerModel(BaseModel):
    __tablename__ = "question_answer_sub_question_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    question_answer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("question_answers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_answer_helper_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("question_answer_helpers.id", ondelete="CASCADE"), nullable=False, index=True
    )
