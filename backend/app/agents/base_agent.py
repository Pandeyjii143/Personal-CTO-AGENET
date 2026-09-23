import json

from app.agents.openai_client import client
from app.core.settings import settings
from app.core.agent_config import AGENT_CONFIG


class BaseAgent:

    MAX_PROMPT_LENGTH = 10000

    @classmethod
    def get_model(cls):
        return AGENT_CONFIG.get(
            cls.__name__,
            {}
        ).get(
            "model",
            settings.openai_model
        )

    @classmethod
    def get_max_output_tokens(cls):
        return AGENT_CONFIG.get(
            cls.__name__,
            {}
        ).get(
            "max_output_tokens",
            6000
        )

    @classmethod
    def call_llm(cls, prompt: str):

        if not prompt:
            raise ValueError(
                "Prompt cannot be empty"
            )

        if len(prompt) > cls.MAX_PROMPT_LENGTH:
            raise ValueError(
                f"Prompt too large ({len(prompt)} chars)"
            )

        try:

            model = cls.get_model()
            max_tokens = cls.get_max_output_tokens()

            response = client.responses.create(
                model=model,
                input=prompt,
                max_output_tokens=max_tokens
            )

            if hasattr(response, "usage"):
                print(
                    f"{cls.__name__} | "
                    f"Model: {model} | "
                    f"Input Tokens: {response.usage.input_tokens} | "
                    f"Output Tokens: {response.usage.output_tokens}"
                )

            return response.output_text

        except Exception as e:
            print(
                f"{cls.__name__} ERROR: {e}"
            )

            raise Exception(
                f"{cls.__name__} failed: {str(e)}"
            )

    @staticmethod
    def parse_json(response: str):

        try:
            response = (
                response
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            return json.loads(response)

        except Exception as e:

            print("JSON PARSE ERROR")
            print(response)

            return {
                "success": False,
                "raw_response": response,
                "error": str(e)
            }