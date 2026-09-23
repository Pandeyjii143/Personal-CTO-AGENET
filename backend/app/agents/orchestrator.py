from app.agents.jev_workflow_evaluator import (
    JevWorkflowEvaluator
)

from app.agents.jev_risk_evaluator import (
    JevRiskEvaluator
)

from app.agents.jev_router import JevRouter

from app.models.execution_context import (
    ExecutionContext
)

from app.agents.backend_agent import BackendAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.architect_agent import ArchitectAgent
from app.agents.ai_agent import AIAgent
from app.agents.devops_agent import DevOpsAgent
from app.agents.testing_agent import TestingAgent


AGENTS = {
    "backend_agent": BackendAgent,
    "frontend_agent": FrontendAgent,
    "architect_agent": ArchitectAgent,
    "ai_agent": AIAgent,
    "devops_agent": DevOpsAgent,
    "testing_agent": TestingAgent,
}


class Orchestrator:

    @staticmethod
    def execute(task: str):

        route = JevRouter.route(task)

        workflow = JevWorkflowEvaluator.evaluate(task)

        risk = JevRiskEvaluator.evaluate(task)

        result = None

        if workflow["workflow_type"] == "single_agent":

            agent_name = route["selected_agent"]

            agent = AGENTS[agent_name]

            result = agent.execute(task)

        else:

            results = {}

            context = ExecutionContext(
                task=task
            )

            architecture = ArchitectAgent.generate(
                project_name="Generated Project",
                goal=task
            )

            context.architecture = architecture

            results["architecture"] = architecture

            for agent_name in workflow["required_agents"]:

                if agent_name == "architect_agent":
                    continue

                agent = AGENTS.get(agent_name)

                if agent:

                    results[agent_name] = (
                        agent.execute(context)
                    )

            result = results

        return {
            "route": route,
            "workflow": workflow,
            "risk": risk,
            "result": result
        }