"""Business Unit Master — SQLAlchemy ORM model. id is the first column."""

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class BusinessUnitModel(BaseModel):
    __tablename__ = "business_units"

    # Explicitly re-declare id first so PostgreSQL puts it as column 1
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
