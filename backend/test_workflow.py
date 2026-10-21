from app.services.workflow_service import WorkflowService

workflow = WorkflowService.create(
    "Build AI Expense Tracker SaaS"
)

print(workflow.model_dump())