from app.agents.base_agent import BaseAgent

FRONTEND_PROMPT = """
You are a senior Next.js engineer.

Task:
{task}

Generate implementation plan and code.
"""


class FrontendAgent(BaseAgent):

    @classmethod
    def execute(cls, task):

        prompt = FRONTEND_PROMPT.format(
            task=task
        )

        return cls.call_llm(prompt)