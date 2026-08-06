"""SQLAlchemy ORM models for the workflow engine."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import Base, BaseModel


class WorkflowDefinitionModel(BaseModel):
    __tablename__ = "workflow_definitions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkflowStatusModel(BaseModel):
    __tablename__ = "workflow_statuses"
    __table_args__ = (
        UniqueConstraint("workflow_definition_id", "code", name="uq_workflow_statuses_definition_code"),
    )

    workflow_definition_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class WorkflowTransitionModel(BaseModel):
    __tablename__ = "workflow_transitions"
    __table_args__ = (
        UniqueConstraint(
            "workflow_definition_id", "from_status_id", "action_code",
            name="uq_workflow_transitions_from_action",
        ),
    )

    workflow_definition_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_statuses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_status_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_statuses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(20), default="CUSTOM", nullable=False)
    guard_expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_comment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_execute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class WorkflowInstanceModel(BaseModel):
    __tablename__ = "workflow_instances"

    workflow_definition_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    current_status_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_statuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    initiated_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    extra_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    approval_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class WorkflowHistoryModel(Base):
    """
    Append-only trail of executed transitions.
    Uses Base (not BaseModel) — history rows are never updated.
    id is BIGSERIAL.
    """

    __tablename__ = "workflow_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    instance_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    to_status_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actor_username: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    comments: Mapped[str] = mapped_column(Text, default="", nullable=False)
    extra_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
