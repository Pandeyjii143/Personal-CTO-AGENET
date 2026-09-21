from app.agents.base_agent import BaseAgent
from app.core.prompts import TASK_PROMPT
import json


class TaskAgent(BaseAgent):

    @staticmethod
    def generate(
        project_name: str,
        milestone_title: str,
        milestone_description: str
    ):

        prompt = TASK_PROMPT.format(
            project_name=project_name,
            milestone_title=milestone_title,
            milestone_description=milestone_description
        )

        response = BaseAgent.call_llm(prompt)

        return json.loads(response)