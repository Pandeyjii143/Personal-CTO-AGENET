from openai import OpenAI
from app.core.settings import settings

client = OpenAI(
    api_key=settings.openai_api_key
)