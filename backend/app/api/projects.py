from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse
)
from app.services.project_service import (
    ProjectService
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.post(
    "",
    response_model=ProjectResponse
)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db)
):
    return ProjectService.create_project(
    db=db,
    name=data.name,
    description=data.description,
    goal=data.goal
)


@router.get(
    "",
    response_model=list[ProjectResponse]
)
def get_projects(
    db: Session = Depends(get_db)
):
    return ProjectService.get_projects(db)

@router.get(
    "/{project_id}",
    response_model=ProjectResponse
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    return ProjectService.get_project(
        db,
        project_id
    )