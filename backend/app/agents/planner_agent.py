from app.agents.base_agent import BaseAgent
from app.core.prompts import PLANNER_PROMPT

import json


class PlannerAgent(BaseAgent):

    @classmethod
    def generate(
        cls,
        project_name: str,
        goal: str
    ):

        prompt = PLANNER_PROMPT.format(
            project_name=project_name,
            goal=goal
        )

        response = cls.call_llm(prompt)

        return json.loads(response)