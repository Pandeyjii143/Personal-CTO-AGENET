from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str
    goal: str


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    goal: str
    status: str
    progress: int

    model_config = {
        "from_attributes": True
    }