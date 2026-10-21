from fastapi import APIRouter
from app.agents.openai_client import get_openai_client

from fastapi import APIRouter
from app.agents.architect_agent import ArchitectAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.task_agent import TaskAgent
from app.agents.jev_router import JevRouter
from app.agents.jev_complexity_evaluator import JevComplexityEvaluator
from app.agents.jev_risk_evaluator import JevRiskEvaluator
from app.agents.jev_architecture_reviewer import (
    JevArchitectureReviewer
)
from app.agents.jev_completion_validator import (
    JevCompletionValidator
)
from app.agents.orchestrator import (
    Orchestrator
)
from app.services.validator_service import ValidatorService

ai_test_router = APIRouter(
    prefix="/ai",
    tags=["AI Test"]
)
from app.agents.requirement_agent import RequirementAgent

@ai_test_router.get("/architect-test")
def architect_test():

    return ArchitectAgent.generate(
        project_name="Personal CTO",
        goal="Build AI powered project management SaaS"
    )
@ai_test_router.get("/ai-test")
def ai_test():

    response = get_openai_client().responses.create(
        model="gpt-5.6",
        input="Say hello CTO"
    )

    return {
        "response": response.output_text
    }

@ai_test_router.get("/planner-test")
def planner_test():

    return PlannerAgent.generate(
        project_name="Personal CTO",
        goal="Build AI powered project management SaaS"
    )

@ai_test_router.get("/planner-test")
def planner_test():

    return PlannerAgent.generate(
        project_name="Personal CTO",
        goal="Build AI powered SaaS"
    )

@ai_test_router.get("/task-test")
def task_test():

    return TaskAgent.generate(
    "Personal CTO AI",
    "Build Authentication",
    "Implement user registration, login, JWT authentication and password reset"
)

@ai_test_router.get("/router-test")
def router_test():

    return JevRouter.route(
        "Build JWT authentication system using FastAPI"
    )

@ai_test_router.get("/complexity-test")
def complexity_test():

    return JevComplexityEvaluator.evaluate(
        "Build an AI SaaS with FastAPI, Next.js and Docker deployment"
    )

@ai_test_router.get("/risk-test")
def risk_test():

    return JevRiskEvaluator.evaluate(
        "Delete all production database records"
    )

@ai_test_router.get("/review-test")
def review_test():

    architecture = """
    FastAPI Backend
    PostgreSQL
    Next.js Frontend
    OpenAI Integration
    Docker Deployment
    """

    return JevArchitectureReviewer.review(
        architecture
    )

@ai_test_router.get("/completion-test")
def completion_test():

    return JevCompletionValidator.validate(
        task="Build JWT Authentication",
        output="""
        Created Login API
        Created Register API
        Added JWT Token
        Protected Routes
        """
    )

@ai_test_router.get("/orchestrator-test")
def orchestrator_test():

    return Orchestrator.execute(
        "Build JWT authentication system using FastAPI"
    )


@ai_test_router.get("/validator-test")
def validator_test():

    report = ValidatorService.validate_project(
        project_folder="generated_projects/generated_project_20260923_195528"
    )

    return report
