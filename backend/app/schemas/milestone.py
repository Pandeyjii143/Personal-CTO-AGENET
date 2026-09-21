from pydantic import BaseModel
from typing import List

class MilestoneResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str
    status: str
    order_index: int

    model_config = {
        "from_attributes": True
    }
