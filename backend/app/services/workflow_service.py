from app.models.workflow_state import WorkflowState


class WorkflowService:

    @staticmethod
    def create(task: str):
        return WorkflowState(
            task=task
        )