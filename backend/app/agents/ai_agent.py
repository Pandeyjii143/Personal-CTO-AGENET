from app.agents.base_agent import BaseAgent

AI_PROMPT = """
You are an AI integration specialist.

Task:
{task}

Design AI solution.
"""


class AIAgent(BaseAgent):

    @classmethod
    def execute(cls, task):

        prompt = AI_PROMPT.format(
            task=task
        )

        return cls.call_llm(prompt)