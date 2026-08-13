"""Format Master — SQLAlchemy ORM model. Table: formats."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class FormatModel(BaseModel):
    __tablename__ = "formats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    format_no: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    format_title: Mapped[str] = mapped_column(String(255), nullable=False)
    format_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("units.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    format_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    has_declaration_question: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
