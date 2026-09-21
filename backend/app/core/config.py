from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    app_version: str
    environment: str

    database_url: str
    openai_api_key: str

    # ADD THIS
    openai_model: str = "gpt-5.6"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()