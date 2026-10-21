from typing import Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FastAPI JWT Auth"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False

    database_url: str = "sqlite:///./app.db"

    secret_key: str = Field(
        default="change-this-insecure-development-secret",
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET_KEY"),
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.environment == "production" and (
            self.secret_key == "change-this-insecure-development-secret"
            or len(self.secret_key) < 32
        ):
            raise ValueError(
                "Production requires a SECRET_KEY of at least 32 characters."
            )
        return self


settings = Settings()
