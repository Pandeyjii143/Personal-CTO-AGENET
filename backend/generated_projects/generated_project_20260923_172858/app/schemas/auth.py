from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AuthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128, repr=False)


class RegisterRequest(AuthRequest):
    password: str = Field(min_length=8, max_length=128, repr=False)


class LoginRequest(AuthRequest):
    pass


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = Field(default=None, gt=0)


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sub: str
    exp: int | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    email: EmailStr
    is_active: bool = True
