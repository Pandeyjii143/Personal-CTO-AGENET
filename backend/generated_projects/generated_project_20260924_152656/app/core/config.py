from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "FastAPI Authentication API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str = "development-only-change-this-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if (
            self.ENVIRONMENT.lower() == "production"
            and self.SECRET_KEY == "development-only-change-this-secret-key"
        ):
            raise ValueError("SECRET_KEY must be configured in production")
        return self


@lru_cache
 def get_settings() -> Settings:
    return Settings()


settings = get_settings()
