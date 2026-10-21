from openai import OpenAI

from app.agents.base_agent import BaseAgent


class RepairAgent(BaseAgent):

    @classmethod
    def execute(
        cls,
        validation_report,
        file_contents,
        test_report=None,
        llm_client: OpenAI | None = None,
    ):

        prompt = f"""
You are a senior software engineer.

Fix the project.

Validation Report:
{validation_report}

Test Report:
{test_report or "No test failures"}

Files:
{file_contents}

Rules:

1. Fix only reported errors.
2. Preserve architecture.
3. Do not rewrite unrelated files.
4. Return only changed files.
5. Return valid JSON.

Format:

{{
  "files": [
    {{
      "file_path": "",
      "code": ""
    }}
  ]
}}
"""
        

        response = cls.call_llm(prompt, llm_client)

        return cls.parse_json(response)