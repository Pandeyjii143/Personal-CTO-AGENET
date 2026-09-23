from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FastAPI JWT Authentication"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False

    # Set SECRET_KEY to a securely generated value of at least 32 characters.
    secret_key: SecretStr
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_issuer: str | None = None
    jwt_audience: str | None = None

    database_url: str = "sqlite:///./app.db"
    cors_origins: list[str] = []

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key_length(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return value

    @field_validator("access_token_expire_minutes", "refresh_token_expire_days")
    @classmethod
    def validate_positive_token_lifetime(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Token lifetimes must be greater than zero")
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment == "production" and self.debug:
            raise ValueError("DEBUG must be false in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


settings = get_settings()
