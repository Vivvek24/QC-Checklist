"""Question Master — ORM models. Tables: questions + question_sub_questions junction."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database.models.base_model import BaseModel


class QuestionModel(BaseModel):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    answer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    has_text_box: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_multiple_text_box: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_sub_question: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_validation_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_response_option: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_multiple_input: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_associated_master: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_calculated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    validation_type_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("validation_types.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_question_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    master_type: Mapped[str | None] = mapped_column(String(50), nullable=True)


class QuestionSubQuestionModel(BaseModel):
    """Junction table: question ↔ sub-questions (many-to-many self-join)."""

    __tablename__ = "question_sub_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    question_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sub_question_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
