from pydantic import BaseModel


class TaskResponse(BaseModel):
    id: int
    project_id: int
    milestone_id: int

    title: str
    description: str

    status: str
    priority: str

    order_index: int

    model_config = {
        "from_attributes": True
    }