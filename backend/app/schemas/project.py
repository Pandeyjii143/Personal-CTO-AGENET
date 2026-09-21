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

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    goal: str | None = None
    status: str | None = None
    progress: int | None = None