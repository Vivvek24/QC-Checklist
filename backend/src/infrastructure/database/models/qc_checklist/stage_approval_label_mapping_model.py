"""StageApprovalLabelMapping — SQLAlchemy ORM model. Table: stage_approval_label_mappings."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class StageApprovalLabelMappingModel(BaseModel):
    __tablename__ = "stage_approval_label_mappings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    checklist_stage_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checklist_stages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approval_label_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("approval_labels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    remark_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("remarks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    role_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    date_of_action: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remark: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_show: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_refer_back: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
