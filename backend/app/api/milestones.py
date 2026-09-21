from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.milestone import (
    MilestoneResponse
)
from app.services.milestone_service import (
    MilestoneService
)

router = APIRouter(
    prefix="/projects",
    tags=["Milestones"]
)

@router.post(
    "/{project_id}/generate-milestones",
    response_model=list[MilestoneResponse]
)
def generate_milestones(
    project_id: int,
    db: Session = Depends(get_db)
):
    return MilestoneService.generate_milestones(
        db,
        project_id
    )

@router.get(
    "/{project_id}/milestones",
    response_model=list[MilestoneResponse]
)
def get_milestones(
    project_id: int,
    db: Session = Depends(get_db)
):
    return MilestoneService.get_milestones(
        db,
        project_id
    )