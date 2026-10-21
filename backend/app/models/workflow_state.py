from pydantic import BaseModel
from typing import Optional


class WorkflowState(BaseModel):
    task: str

    requirement: Optional[dict] = None

    architecture: Optional[dict] = None

    milestones: Optional[list] = None

    generated_files: Optional[dict] = None

    status: str = "created"

    approved: bool = False