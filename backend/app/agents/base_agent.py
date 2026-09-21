from app.agents.openai_client import client
from app.core.settings import settings


class BaseAgent:

    MODEL = settings.openai_model

    @classmethod
    def call_llm(cls, prompt: str):

        response = client.responses.create(
            model=cls.MODEL,
            input=prompt
        )

        return response.output_text