"""Approval Label Master — ORM models. Tables: approval_labels + approval_label_user_roles junction."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database.models.base_model import BaseModel


class ApprovalLabelModel(BaseModel):
    __tablename__ = "approval_labels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Nullable: a label belongs to EITHER a stage OR a question (question master
    # mirror of the stage approval-label pattern), so one of stage_id/question_id
    # is set and the other is NULL.
    stage_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("stages.id", ondelete="RESTRICT"), nullable=True, index=True)
    # An approval label can also belong to a question (question master mirror of
    # the stage approval-label pattern). Nullable so existing stage-level labels
    # are unaffected.
    question_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ApprovalLabelUserRoleModel(BaseModel):
    __tablename__ = "approval_label_user_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    approval_label_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("approval_labels.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
