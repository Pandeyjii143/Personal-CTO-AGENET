from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Credentials and identity information for creating a user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Credentials used to authenticate a user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    """Bearer access token returned after successful authentication."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"


class TokenData(BaseModel):
    """Identity claims extracted from a validated access token."""

    sub: str | None = None


class UserResponse(BaseModel):
    """Public user data; credentials are never included."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool = True
