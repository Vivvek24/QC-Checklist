"""Template — SQLAlchemy ORM models.

Tables: templates, template_layout_columns.

`templates` is the anchor for a format's checklist design (one row per
format, for now). `template_layout_columns` holds every column flat, each row
carrying its own format_stage_mapping_id/section_id scope directly — no
intermediate per-scope parent row.
"""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class TemplateModel(BaseModel):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    format_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("formats.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TemplateLayoutColumnModel(BaseModel):
    __tablename__ = "template_layout_columns"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    template_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    format_stage_mapping_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("format_stage_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # NULL => stage-level column; a value => section-level column.
    section_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    header: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    column_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ANSWER")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    width: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
