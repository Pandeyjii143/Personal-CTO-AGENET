from app.agents.openai_client import client
from app.core.prompts import ARCHITECT_PROMPT
import json
from app.core.settings import settings
from app.agents.base_agent import BaseAgent

class ArchitectAgent(BaseAgent):

    @staticmethod
    def generate(
        project_name: str,
        goal: str,
        cls
    ):

        prompt = ARCHITECT_PROMPT.format(
            project_name=project_name,
            goal=goal
        )

        response = cls.call_llm(prompt)

        return json.loads(
            response.output_text
        )