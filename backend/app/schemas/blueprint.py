from pydantic import BaseModel


class BlueprintResponse(BaseModel):
    id: int
    project_id: int
    architecture: dict
    tech_stack: list
    risks: list
    status: str

    model_config = {
        "from_attributes": True
    }