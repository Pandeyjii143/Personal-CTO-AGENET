import json

from app.agents.base_agent import BaseAgent
from app.core.prompts import WORKFLOW_EVALUATOR_PROMPT


class JevWorkflowEvaluator(BaseAgent):

    @classmethod
    def evaluate(
        cls,
        task: str
    ):

        prompt = WORKFLOW_EVALUATOR_PROMPT.format(
            task=task
        )

        result = cls.call_llm(prompt)

        return json.loads(result)