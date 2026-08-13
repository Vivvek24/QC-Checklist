"""StageQuestionMapping — SQLAlchemy ORM model. Table: stage_question_mappings."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class StageQuestionMappingModel(BaseModel):
    __tablename__ = "stage_question_mappings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    format_stage_mapping_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("format_stage_mappings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sap_field_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sap_fields.id", ondelete="SET NULL"), nullable=True, index=True
    )
    section_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    serial_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    show_on_grid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    aql_limit: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    is_declaration_question: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    custom_answers: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
