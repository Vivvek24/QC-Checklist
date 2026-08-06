"""
SQLAlchemy declarative base with audit mixin.
All ORM models inherit from this to get automatic audit field population.
Primary keys are BigInteger (auto-increment), not UUID.
"""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""
    pass


class AuditMixin:
    """
    Mixin providing BigInteger primary key and audit columns for all models.

    id is BIGSERIAL (auto-increment) — the database generates it on INSERT.
    Do not pass id when creating a model; flush to get the generated value.
    """

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(
        String(255), nullable=False, default="system"
    )
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    modified_by: Mapped[str] = mapped_column(
        String(255), nullable=False, default="system"
    )
    modified_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class BaseModel(AuditMixin, Base):
    """
    Abstract base model combining DeclarativeBase with BigInt PK and audit fields.
    All concrete models should inherit from this.
    """
    __abstract__ = True
