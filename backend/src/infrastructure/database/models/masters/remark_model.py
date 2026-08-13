"""Remark Master — ORM models. Table: remarks + remark_user_roles junction."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class RemarkModel(BaseModel):
    __tablename__ = "remarks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    remark: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RemarkUserRoleModel(BaseModel):
    """Junction table: remarks ↔ roles (many-to-many)."""

    __tablename__ = "remark_user_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    remark_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("remarks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
