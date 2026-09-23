from app.agents.base_agent import BaseAgent

DEVOPS_PROMPT = """
You are a DevOps engineer.

Task:
{task}

Generate deployment plan.
"""


class DevOpsAgent(BaseAgent):

    @classmethod
    def execute(cls, task):

        prompt = DEVOPS_PROMPT.format(
            task=task
        )

        return cls.call_llm(prompt)