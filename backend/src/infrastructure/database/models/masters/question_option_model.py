"""QuestionOption Master — SQLAlchemy ORM model. Table: question_options."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class QuestionOptionModel(BaseModel):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    option_title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    is_response_option: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    question_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
