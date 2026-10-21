# app/agents/readme_agent.py

from openai import OpenAI

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
    def execute(cls, context, llm_client: OpenAI | None = None):
        prompt = README_PROMPT.format(
            task=context.task,
            backend_summary=context.backend_plan["backend_summary"]
        )

        response = cls.call_llm(prompt, llm_client)

        return cls.parse_json(response)