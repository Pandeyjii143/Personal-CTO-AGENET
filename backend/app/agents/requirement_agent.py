from app.agents.base_agent import BaseAgent


REQUIREMENT_PROMPT = """
You are a senior CTO.

Analyze the user project request.

Return JSON only.

{{
    "project_name":"",
    "description":"",
    "frontend":true,
    "backend":true,
    "ai":false,
    "database":"postgresql",
    "deployment":"docker"
}}

User Request:

{task}
"""


class RequirementAgent(BaseAgent):

    @classmethod
    def execute(cls, task: str):

        prompt = REQUIREMENT_PROMPT.format(
            task=task
        )

        response = cls.call_llm(prompt)

        return cls.parse_json(response)