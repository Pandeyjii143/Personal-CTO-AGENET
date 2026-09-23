import json

from app.agents.base_agent import BaseAgent
from app.core.prompts import COMPLETION_VALIDATOR_PROMPT


class JevCompletionValidator(BaseAgent):

    @classmethod
    def validate(
        cls,
        task: str,
        output: str
    ):

        prompt = COMPLETION_VALIDATOR_PROMPT.format(
            task=task,
            output=output
        )

        result = cls.call_llm(prompt)

        return json.loads(result)