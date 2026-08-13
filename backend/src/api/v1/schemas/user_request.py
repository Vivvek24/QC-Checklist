"""User request schemas (Pydantic v2)."""

from pydantic import BaseModel, EmailStr, Field


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., max_length=128)
    is_validate_ad: bool = Field(default=True)
    role_id: int | None = Field(default=None)


class UpdateUserRequest(BaseModel):
    is_active: bool | None = None
    is_blocked: bool | None = None
    is_validate_ad: bool | None = None
    role_id: int | None = Field(default=None)
    email: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=128)
