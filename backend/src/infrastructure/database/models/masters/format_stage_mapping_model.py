"""FormatStageMapping — SQLAlchemy ORM model. Table: format_stage_mappings."""

from sqlalchemy import BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class FormatStageMappingModel(BaseModel):
    __tablename__ = "format_stage_mappings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    format_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("formats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_approvable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_refer_back: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_section: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
