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
from datetime import datetime

from app.agents.backend_agent import BackendAgent
from app.agents.backend_code_agent import BackendCodeAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.architect_agent import ArchitectAgent
from app.agents.ai_agent import AIAgent
from app.agents.devops_agent import DevOpsAgent
from app.agents.testing_agent import TestingAgent

from app.services.file_writer import FileWriter
from app.services.project_runner import ProjectRunner


AGENTS = {
    "backend_agent": BackendAgent,
    "backend_code_agent": BackendCodeAgent,
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

        workflow = JevWorkflowEvaluator.evaluate(
            task
        )

        risk = JevRiskEvaluator.evaluate(
            task
        )

        results = {}

        if workflow["workflow_type"] == "single_agent":

            agent_name = route["selected_agent"]

            if agent_name == "backend_agent":

                # ----------------------------------
                # Create Context
                # ----------------------------------

                context = ExecutionContext(
                    task=task
                )

                # ----------------------------------
                # Step 1: Backend Planning
                # ----------------------------------

                backend_plan = BackendAgent.execute(
                    task
                )

                context.backend_plan = (
                    backend_plan
                )

                results["backend_plan"] = (
                    backend_plan
                )

                # ----------------------------------
                # Step 2: Generate Files
                # ----------------------------------

                generated_files = {}

                required_files = (
                    backend_plan.get(
                        "required_files",
                        []
                    )
                )

                print(
                    f"Required Files Count: "
                    f"{len(required_files)}"
                )

                print(required_files)

                for i, file_path in enumerate(
                    required_files
                ):

                    print(
                        f"[{i+1}/{len(required_files)}] "
                        f"Generating {file_path}"
                    )

                    code_result = (
                        BackendCodeAgent.execute(
                            context=context,
                            file_path=file_path
                        )
                    )

                    generated_files[
                        file_path
                    ] = code_result

                context.generated_files = (
                    generated_files
                )

                results["generated_files"] = (
                    generated_files
                )

               # ----------------------------------
                # Step 3: Save Files
                # ----------------------------------

                

                project_name = (
                    backend_plan.get(
                        "project_name",
                        "generated_project"
                    )
                )

                project_name = (
                    f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )

                print("PROJECT NAME =", project_name)

                FileWriter.write_files(
                    generated_files,
                    project_name
                )

                results["project_folder"] = (
                    f"generated_projects/{project_name}"
                )

                print(
                    f"Project saved in generated_projects/{project_name}"
                )

                # ----------------------------------
                # Step 4: Run Tests
                # ----------------------------------

                test_result = (
                    ProjectRunner.run_tests()
                )

                results["test_result"] = (
                    test_result
                )

                print(
                    "Tests Success:",
                    test_result["success"]
                )

            else:

                agent = AGENTS[agent_name]

                results[agent_name] = (
                    agent.execute(task)
                )

        return {
            "route": route,
            "workflow": workflow,
            "risk": risk,
            "result": results
        }