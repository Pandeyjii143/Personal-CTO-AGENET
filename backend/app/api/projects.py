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

from app.schemas.project import ProjectUpdate
from fastapi import HTTPException

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

@router.patch(
    "/{project_id}",
    response_model=ProjectResponse
)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    project = ProjectService.update_project(
        db,
        project_id,
        data.model_dump(exclude_unset=True)
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return project

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    deleted = ProjectService.delete_project(
        db,
        project_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return {
        "message": f"Project id:{project_id} deleted successfully"
    }