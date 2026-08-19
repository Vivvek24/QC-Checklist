"""QuestionAnswer — SQLAlchemy ORM model. Table: question_answers."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class QuestionAnswerModel(BaseModel):
    __tablename__ = "question_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    checklist_stage_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checklist_stages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    checklist_stage_section_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("checklist_stage_sections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    question_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    question_option_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("question_options.id", ondelete="SET NULL"), nullable=True, index=True
    )
    receiver_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    response_question_option_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("question_options.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stage_question_mapping_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("stage_question_mappings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    textbox_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    response_answer: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    comma_separated_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    has_helper: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    serial_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sub_answer_serial_no: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    date_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    test_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    sample_vails: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    answer_total_vails: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issued_by_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issuer_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_issued_vails: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_vails: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
