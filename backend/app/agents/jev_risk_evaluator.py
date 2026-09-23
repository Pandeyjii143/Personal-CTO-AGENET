import json

from app.agents.base_agent import BaseAgent
from app.core.prompts import JEV_RISK_PROMPT


class JevRiskEvaluator(BaseAgent):

    @classmethod
    def evaluate(cls, action: str):

        prompt = JEV_RISK_PROMPT.format(
            action=action
        )

        response = cls.call_llm(prompt)

        return cls.parse_json(response)