import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Set SECRET_KEY explicitly in deployed environments. The generated fallback
    # is suitable only for local development and changes each time the app starts.
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        min_length=32,
        repr=False,
    )
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)

    DATABASE_URL: str = "sqlite:///./app.db"


@lru_cache
 def get_settings() -> Settings:
    return Settings()


settings = get_settings()
