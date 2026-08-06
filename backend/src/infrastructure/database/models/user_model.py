"""SQLAlchemy ORM model for the User entity."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base_model import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_validate_ad: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
