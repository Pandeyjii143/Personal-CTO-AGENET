from openai import OpenAI

from app.agents.base_agent import BaseAgent

BACKEND_CODE_PROMPT = """
You are a senior FastAPI engineer.

Project:
{task} 

Backend Architecture:
{backend_summary}

Generate ONLY the code for:

{file_path}

Return JSON:

{{
    "file_path":"",
    "code":""
}}
"""


class BackendCodeAgent(BaseAgent):

    @classmethod
    def execute(
        cls,
        context,
        file_path,
        llm_client: OpenAI | None = None,
    ):

        prompt = BACKEND_CODE_PROMPT.format(
            task=context.task,
            backend_summary=
                context.backend_plan[
                    "backend_summary"
                ],
            file_path=file_path
        )

        response = cls.call_llm(prompt, llm_client)

        return cls.parse_json(response)