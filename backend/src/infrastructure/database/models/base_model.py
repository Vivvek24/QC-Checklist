"""
SQLAlchemy declarative base with audit mixin.
Primary keys are BigInteger (auto-increment), not UUID.

NOTE on column ordering: SQLAlchemy places subclass mapped_columns before
mixin mapped_columns in the DDL. To guarantee id is always the FIRST column,
each concrete model must NOT define any columns before id. The convention is
that id, created_by, created_date, modified_by, modified_date are all from
the mixin and concrete models only define their own business columns — which
will appear after the mixin columns because SQLAlchemy processes the MRO
such that Base (mixin) columns come first when using __abstract__ correctly.

The key is: BaseModel uses __abstract__ = True so its columns ARE inherited
and appear first in the ORM column order.
"""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    """
    Abstract base model. id BIGSERIAL is the first column.
    Concrete models inherit this and add their own columns after.
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    modified_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
    modified_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
