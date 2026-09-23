from app.agents.base_agent import BaseAgent

BACKEND_PROMPT = """
You are a senior FastAPI backend engineer.

Task:
{task}

Generate implementation plan and code.
"""


class BackendAgent(BaseAgent):

    @classmethod
    def execute(cls, task):

        prompt = BACKEND_PROMPT.format(
            task=task
        )

        return cls.call_llm(prompt)