import json

from app.agents.openai_client import client
from app.core.settings import settings


class BaseAgent:
    MODEL = settings.openai_model

    @classmethod
    def call_llm(cls, prompt: str):

        try:
            response = client.responses.create(
                model=cls.MODEL,
                input=prompt
            )

            return response.output_text

        except Exception as e:
            print(f"LLM ERROR: {e}")
            raise Exception(
                f"{cls.__name__} failed: {str(e)}"
            )
    @staticmethod
    def parse_json(response: str):

        response = (
            response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        return json.loads(response)