from app.agents.base_agent import BaseAgent

HITL_PROMPT = """
You are a Human-In-The-Loop approval agent.

Your job is NOT to do project discovery.

Your job is to ask only the minimum questions required before code generation.

Return JSON only.

{{
    "approved": false,
    "questions": [
        ""
    ]
}}

Project Configuration:

{config}

Rules:

- Ask at most 5 questions.
- Do not ask about architecture.
- Do not ask about security.
- Do not ask about compliance.
- Do not ask open-ended consulting questions.

Only ask things like:

- Create frontend?
- Create backend?
- Create AI features?
- Create new GitHub repository or use existing repository?
- If existing repository, provide repository URL.
- Generate README?
- Continue generation?

"""
class HITLAgent(BaseAgent):

    @classmethod
    def execute(cls, config):

        prompt = HITL_PROMPT.format(
            config=config
        )

        response = cls.call_llm(prompt)

        return cls.parse_json(response)