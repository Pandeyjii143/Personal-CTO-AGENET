import json

from app.agents.base_agent import BaseAgent
from app.core.prompts import JEV_ROUTER_PROMPT


class JevRouter(BaseAgent):

    @classmethod
    def route(
        cls,
        task: str
    ):

        prompt = JEV_ROUTER_PROMPT.format(
            task=task
        )

        response = cls.call_llm(prompt)

        return json.loads(response)