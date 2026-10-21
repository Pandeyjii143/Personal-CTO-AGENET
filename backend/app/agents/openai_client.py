from openai import OpenAI
from app.core.settings import settings

configured_api_key = settings.openai_api_key.strip()
client = OpenAI(api_key=configured_api_key) if configured_api_key else None


def get_openai_client(api_key: str | None = None) -> OpenAI:
    if api_key is not None:
        normalized_key = api_key.strip()
        if normalized_key:
            return OpenAI(api_key=normalized_key)

    if client is None:
        raise ValueError("OpenAI API key is not configured")

    return client