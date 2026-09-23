from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FastAPI Authentication API"
    api_v1_prefix: str = "/api/v1"

    # Configure SECRET_KEY in the environment or .env; never use a committed default.
    secret_key: SecretStr = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)

    database_url: str = "sqlite+aiosqlite:///./app.db"


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
