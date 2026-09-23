import json

from app.agents.base_agent import BaseAgent
from app.core.prompts import ARCHITECTURE_REVIEW_PROMPT


class JevArchitectureReviewer(BaseAgent):

    @classmethod
    def review(
        cls,
        architecture_output: str
    ):
        prompt = ARCHITECTURE_REVIEW_PROMPT.format(
            architecture_output=architecture_output
        )

        result = cls.call_llm(prompt)

        return json.loads(result)