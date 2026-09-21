from fastapi import APIRouter
from app.agents.openai_client import client

from fastapi import APIRouter
from app.agents.architect_agent import ArchitectAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.task_agent import TaskAgent

ai_test_router = APIRouter(
    prefix="/ai",
    tags=["AI Test"]
)

@ai_test_router.get("/architect-test")
def architect_test():

    return ArchitectAgent.generate(
        project_name="Personal CTO",
        goal="Build AI powered project management SaaS"
    )
@ai_test_router.get("/ai-test")
def ai_test():

    response = client.responses.create(
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