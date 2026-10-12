"""ChecklistPdfExport — SQLAlchemy ORM model. Table: checklist_pdf_exports.

Audit of PDF exports: one row per export, carrying only which request was
exported. The actor (created_by) and timestamp (created_date) come from the
BaseModel audit columns.
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class ChecklistPdfExportModel(BaseModel):
    __tablename__ = "checklist_pdf_exports"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )
    request_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
