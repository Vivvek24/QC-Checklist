"""ChecklistStageSection — SQLAlchemy ORM model. Table: checklist_stage_sections."""

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class ChecklistStageSectionModel(BaseModel):
    __tablename__ = "checklist_stage_sections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    checklist_stage_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("checklist_stages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
