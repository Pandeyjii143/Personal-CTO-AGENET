from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_DEVELOPMENT_SECRET = "development-only-secret-key-change-before-deployment"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "FastAPI Authentication API"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    SECRET_KEY: str = Field(default=_DEVELOPMENT_SECRET, min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production" and self.SECRET_KEY == _DEVELOPMENT_SECRET:
            raise ValueError("Set a unique SECRET_KEY before running in production")
        return self


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
