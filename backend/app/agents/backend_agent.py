from openai import OpenAI

from app.agents.base_agent import BaseAgent

BACKEND_PROMPT = """
You are a senior FastAPI backend engineer.

Task:
{task}

Return ONLY:

{{
    "backend_summary":"",
    "required_files":[]
}}

Rules:
1. required_files must contain ONLY file paths.
2. Never return folders or directories.
3. Every item must have a filename and extension.
4. Examples:
   - app/main.py
   - app/models/user.py
   - tests/test_auth.py
   - alembic/env.py
5. Invalid examples:
   - app/
   - alembic/
   - alembic/versions/

Do not generate implementation details.
Do not generate code.
Do not generate endpoints.
Do not generate tasks.
"""

class BackendAgent(BaseAgent):

    @classmethod
    def execute(cls, task, llm_client: OpenAI | None = None):

        prompt = BACKEND_PROMPT.format(
            task=task
        )

        response = cls.call_llm(prompt, llm_client)

        return cls.parse_json(response)