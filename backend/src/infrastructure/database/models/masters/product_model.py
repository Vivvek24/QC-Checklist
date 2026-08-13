"""Product Master — ORM model. Table: products."""

from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database.models.base_model import BaseModel


class ProductModel(BaseModel):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    storage_conditions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
