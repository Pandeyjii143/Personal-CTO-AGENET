from app.agents.base_agent import BaseAgent

TESTING_PROMPT = """
You are a QA engineer.

Task:
{task}

Generate test cases.
"""


class TestingAgent(BaseAgent):

    @classmethod
    def execute(cls, task):

        prompt = TESTING_PROMPT.format(
            task=task
        )

        return cls.call_llm(prompt)