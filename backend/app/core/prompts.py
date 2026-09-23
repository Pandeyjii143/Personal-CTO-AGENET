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

JEV_ROUTER_PROMPT = """
You are the routing engine of a Personal CTO Agent.

Analyze the user request and determine which specialized agent should handle it.

Available Agents:
- architect_agent: System design, architecture, planning, tech stack decisions.
- backend_agent: APIs, databases, backend implementation.
- frontend_agent: UI, React, Next.js, styling.
- ai_agent: LLMs, RAG, embeddings, agents, MCP, LangGraph.
- devops_agent: Docker, CI/CD, deployment, cloud infrastructure.
- testing_agent: Unit tests, integration tests, debugging.
- research_agent: Research and documentation.

Return JSON only.

{{
  "selected_agent": "agent_name",
  "confidence": 0.0,
  "reason": ""
}}

User Request:
{task}
"""
JEV_COMPLEXITY_PROMPT = """
You are a task complexity evaluator.

Available agents:

- architect_agent
- backend_agent
- frontend_agent
- ai_agent
- devops_agent
- testing_agent
- research_agent

Determine whether the task requires one or more of these agents.

Return JSON only.

{{
  "workflow_type": "single_agent | multi_agent",
  "confidence": 0.0,
  "required_agents": [],
  "reason": ""
}}

Task:
{task}
"""

JEV_RISK_PROMPT = """
You are a security and risk evaluator.

Evaluate the proposed action.

Risk Levels:
- low
- medium
- high
- critical

Return JSON only.

{{
  "risk_level": "",
  "confidence": 0.0,
  "requires_human_approval": false,
  "reason": ""
}}

Action:
{action}
"""

ARCHITECTURE_REVIEW_PROMPT = """
You are the CTO architecture reviewer.

Review the proposed architecture.

Evaluate:
- scalability
- maintainability
- security
- performance
- cost efficiency

Return JSON only.

{{
  "approved": true,
  "confidence": 0.0,
  "architecture_score": 1,
  "issues": [],
  "recommendations": []
}}

Architecture:
{architecture_output}
"""

COMPLETION_VALIDATOR_PROMPT = """
You are a task completion validator.

Determine whether the task has been fully completed.

Return JSON only.

{{
  "completed": true,
  "confidence": 0.0,
  "missing_requirements": [],
  "next_action": ""
}}

Original Task:
{task}

Agent Output:
{output}
"""

WORKFLOW_EVALUATOR_PROMPT = """
You are a task complexity evaluator.

Determine whether the task can be completed by a single agent or requires a multi-agent workflow.

Return JSON only.

{{
  "workflow_type": "single_agent | multi_agent",
  "confidence": 0.0,
  "required_agents": [],
  "reason": ""
}}

Task:
{task}
"""