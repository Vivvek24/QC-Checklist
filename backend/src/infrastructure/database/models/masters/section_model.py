"""Section Master — SQLAlchemy ORM model. Table: sections."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class SectionModel(BaseModel):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    section_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    format_stage_mapping_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("format_stage_mappings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
