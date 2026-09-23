from app.agents.openai_client import client
from app.core.prompts import ARCHITECT_PROMPT
import json
from app.core.settings import settings
from app.agents.base_agent import BaseAgent

class ArchitectAgent(BaseAgent):

    @classmethod
    def execute(cls, task: str):

        prompt = ARCHITECT_PROMPT.format(
            project_name="Generated Project",
            goal=task
        )

        response = cls.call_llm(prompt)

        return cls.parse_json(response)

    @classmethod
    def generate(
        cls,
        project_name: str,
        goal: str,
    ):

        prompt = ARCHITECT_PROMPT.format(
            project_name=project_name,
            goal=goal
        )

        response = cls.call_llm(prompt)

        return cls.parse_json(response)