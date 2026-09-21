# app/core/prompts.py

ARCHITECT_PROMPT = """
You are a startup CTO.

Project Name:
{project_name}

Goal:
{goal}

Constraints:
- Solo developer
- FastAPI backend
- PostgreSQL database
- Low cost
- MVP first

Generate valid JSON only.

{{
  "architecture": {{
    "frontend": "",
    "backend": "",
    "database": ""
  }},
  "tech_stack": [],
  "risks": []
}}
"""
PLANNER_PROMPT = """
You are a senior technical project manager.

Project:
{project_name}

Goal:
{goal}

Generate 5-8 milestones.

Return valid JSON only.

[
  {{
    "title": "",
    "description": ""
  }}
]
"""

TASK_PROMPT = """
Project: {project_name}

Milestone: {milestone_title}

Description: {milestone_description}

Return JSON:

{{
    "tasks": [
        {{
            "title": "Setup Backend",
            "description": "Create FastAPI project"
        }}
    ]
}}
"""