"""ChecklistRequest — SQLAlchemy ORM model. Table: checklist_requests."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class ChecklistRequestModel(BaseModel):
    __tablename__ = "checklist_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    request_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    status_format: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_last_stage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sequence_number: Mapped[int] = mapped_column(BigInteger, autoincrement=True, nullable=False)
    approver_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    format_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("formats.id", ondelete="SET NULL"), nullable=True, index=True
    )
