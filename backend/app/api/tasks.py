from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.task import TaskResponse
from app.services.task_service import (
    TaskService
)

router = APIRouter(
    prefix="/milestones",
    tags=["Tasks"]
)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.task import TaskResponse
from app.services.task_service import (
    TaskService
)

router = APIRouter(
    prefix="/milestones",
    tags=["Tasks"]
)

@router.post(
    "/{milestone_id}/generate-tasks",
    response_model=list[TaskResponse]
)
def generate_tasks(
    milestone_id: int,
    db: Session = Depends(get_db)
):
    return TaskService.generate_tasks(
        db,
        milestone_id
    )

@router.get(
    "/{milestone_id}/tasks",
    response_model=list[TaskResponse]
)
def get_tasks(
    milestone_id: int,
    db: Session = Depends(get_db)
):
    return TaskService.get_tasks(
        db,
        milestone_id
    )