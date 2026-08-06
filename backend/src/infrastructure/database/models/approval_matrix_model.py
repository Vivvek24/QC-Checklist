"""SQLAlchemy ORM models for the approval matrix aggregate."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class ApprovalMatrixModel(BaseModel):
    __tablename__ = "approval_matrices"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ApprovalRuleModel(BaseModel):
    __tablename__ = "approval_rules"

    matrix_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("approval_matrices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), default="STRING", nullable=False)
    logical_group: Mapped[str] = mapped_column(String(50), default="default", nullable=False)


class ApprovalAssignmentModel(BaseModel):
    __tablename__ = "approval_assignments"

    matrix_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("approval_matrices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    role_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ApprovalTaskModel(BaseModel):
    __tablename__ = "approval_tasks"
    __table_args__ = (
        UniqueConstraint(
            "instance_id", "assignee_id", "level",
            name="uq_approval_tasks_instance_assignee_level",
        ),
    )

    instance_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matrix_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("approval_matrices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assignee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False, index=True)
    action_taken: Mapped[str | None] = mapped_column(String(50), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
