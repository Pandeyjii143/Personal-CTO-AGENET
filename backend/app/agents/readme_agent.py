# app/agents/readme_agent.py

from app.agents.base_agent import BaseAgent

README_PROMPT = """
You are a senior software architect.

Task:
{task}

Backend Summary:
{backend_summary}

Generate a professional README.md.

Return JSON:

{{
    "file_path": "README.md",
    "code": ""
}}
"""

class READMEAgent(BaseAgent):

    @classmethod
    def execute(cls, context):
        prompt = README_PROMPT.format(
            task=context.task,
            backend_summary=context.backend_plan["backend_summary"]
        )

        response = cls.call_llm(prompt)

        return cls.parse_json(response)