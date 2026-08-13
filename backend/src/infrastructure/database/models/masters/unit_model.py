"""Unit Master — SQLAlchemy ORM model. Table: units."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class UnitModel(BaseModel):
    """
    ORM model for the units table.
    id is BIGSERIAL (first column, auto-generated).
    name is unique per business_unit_id.
    """

    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("name", "business_unit_id", name="uq_units_name_business_unit"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    business_unit_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("business_units.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
