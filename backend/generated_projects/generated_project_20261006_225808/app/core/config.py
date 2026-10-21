from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or an .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FastAPI JWT Authentication"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Override this development default with a strong, private SECRET_KEY in production.
    secret_key: str = "change-this-development-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = "sqlite+aiosqlite:///./app.db"


@lru_cache
 def_placeholder
