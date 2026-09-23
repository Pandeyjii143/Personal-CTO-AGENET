import json

from app.agents.base_agent import BaseAgent
from app.core.prompts import JEV_COMPLEXITY_PROMPT


class JevComplexityEvaluator(BaseAgent):

    @classmethod
    def evaluate(cls, task: str):

        prompt = JEV_COMPLEXITY_PROMPT.format(
            task=task
        )

        response = cls.call_llm(prompt)

        return json.loads(response)