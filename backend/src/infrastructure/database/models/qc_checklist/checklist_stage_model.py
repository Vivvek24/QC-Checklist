"""ChecklistStage — SQLAlchemy ORM model. Table: checklist_stages."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class ChecklistStageModel(BaseModel):
    __tablename__ = "checklist_stages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    checklist_request_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checklist_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    format_stage_mapping_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("format_stage_mappings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Pending")
    performed_remark: Mapped[str] = mapped_column(Text, nullable=False, default="")
    approved_remark: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_self_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    self_verification_details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_approvable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_last_stage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submit_remarks: Mapped[str] = mapped_column(Text, nullable=False, default="")
    self_approved_remark: Mapped[str] = mapped_column(Text, nullable=False, default="")
