"""TestMaster — SQLAlchemy ORM model. Table: test_masters."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class TestMasterModel(BaseModel):
    __tablename__ = "test_masters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sample_description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    sample_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
