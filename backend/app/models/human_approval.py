from pydantic import BaseModel
from typing import List


class HumanApproval(BaseModel):
    approved: bool = False
    questions: List[str] = []
    answers: List[str] = []