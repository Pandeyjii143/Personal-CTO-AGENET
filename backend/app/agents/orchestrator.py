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
import os
from app.services.github_service import GitHubService
from app.agents.readme_agent import READMEAgent
from app.agents.requirement_agent import RequirementAgent
from app.services.hitl_service import HITLService
from app.services.workflow_service import WorkflowService
from app.services.repair_loop_service import (
    RepairLoopService
)


AGENTS = {
    "requirement_agent": RequirementAgent,
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

        workflow = WorkflowService.create(task)


        route = JevRouter.route(task)

        workflow_plan = JevWorkflowEvaluator.evaluate(task)

        risk = JevRiskEvaluator.evaluate(
            task
        )
        hitl_result = HITLService.evaluate(task)

        results = {}

        if workflow_plan["workflow_type"] == "single_agent":

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
                workflow.requirement = backend_plan
                workflow.status = "requirements_completed"

                print(
                    "Requirement Step Completed"
                )
                print(
                    workflow.model_dump()
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
                workflow.generated_files = generated_files
                workflow.status = "code_generated"

                print(
                    "Code Generation Completed"
                )
                print(
                    workflow.model_dump()
                )


                results["generated_files"] = (
                    generated_files
                )

                readme_result = READMEAgent.execute(context)

                generated_files[
                    readme_result["file_path"]
                ] = readme_result

                #          ----------------------------------
                # Step 3: Save Files
                # ----------------------------------

                project_name = (
                    f"generated_project_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )

                project_folder = FileWriter.write_files(
                    generated_files,
                    project_name
                )

                repair_result = (
                RepairLoopService.execute(
                    project_folder
                )
            )

                results["repair_result"] = repair_result

                if not repair_result["success"]:
                  workflow.status = "failed"
                  return {
                      "route": route,
                      "workflow_plan": workflow_plan,
                      "workflow_state": workflow.model_dump(),
                      "risk": risk,
                      "error": "Project validation failed",
                      "repair_result": repair_result
                  }

                results["project_folder"] = project_folder

                print(
                    f"Project saved at {project_folder}"
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
                workflow.status = "completed"

                print(
                    "Workflow Completed"
                )
                print(
                    workflow.model_dump()
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

                # ----------------------------------
                # Step 4.5: Push To GitHub
                # ----------------------------------
                
                repo_url = GitHubService.push_project(
                      project_folder,
                      project_name
                      )
                
                results["repo_url"] = repo_url
                workflow.status = "github_pushed"
                
                print("GitHub Push Completed"
                                )
                print(workflow.model_dump()
                                )
                
                print(f"GitHub Repo: {repo_url}"
                                )

        return {
    "route": route,
    "workflow_plan": workflow_plan,
    "workflow_state": workflow.model_dump(),
    "risk": risk,
    "result": results
}