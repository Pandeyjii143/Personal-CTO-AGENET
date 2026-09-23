from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FastAPI JWT Authentication"
    environment: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False

    database_url: str = "sqlite:///./app.db"

    jwt_secret_key: SecretStr = SecretStr(
        "development-only-change-this-secret-key-before-deployment"
    )
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_origins: list[str] = []

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.access_token_expire_minutes <= 0:
            raise ValueError("access_token_expire_minutes must be greater than zero")
        if self.refresh_token_expire_days <= 0:
            raise ValueError("refresh_token_expire_days must be greater than zero")

        if self.environment == "production":
            secret = self.jwt_secret_key.get_secret_value()
            if secret == "development-only-change-this-secret-key-before-deployment":
                raise ValueError("Set JWT_SECRET_KEY to a unique secret in production")
            if len(secret) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
            if self.debug:
                raise ValueError("DEBUG must be false in production")

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()
