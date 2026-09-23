from app.agents.base_agent import BaseAgent

BACKEND_PROMPT = """
You are a senior FastAPI backend engineer.

Task:
{task}

Return ONLY:

{{
    "backend_summary":"",
    "required_files":[]
}}

Do not generate implementation details.
Do not generate code.
Do not generate endpoints.
Do not generate tasks.
"""


class BackendAgent(BaseAgent):

    @classmethod
    def execute(cls, task):

        prompt = BACKEND_PROMPT.format(
            task=task
        )

        response = cls.call_llm(prompt)

        return cls.parse_json(response)