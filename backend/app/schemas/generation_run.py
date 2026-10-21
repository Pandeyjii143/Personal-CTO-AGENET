from datetime import datetime

from pydantic import BaseModel, Field


class GenerationRunCreate(BaseModel):
    prompt: str = Field(min_length=10, max_length=8000)


class GenerationRunResponse(BaseModel):
    id: int
    prompt: str
    status: str
    project_name: str | None
    result: dict | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
