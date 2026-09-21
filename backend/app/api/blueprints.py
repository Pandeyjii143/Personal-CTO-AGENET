from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.blueprint import BlueprintResponse
from app.services.blueprint_service import (
    BlueprintService
)

router = APIRouter(
    prefix="/projects",
    tags=["Blueprints"]
)


@router.post(
    "/{project_id}/generate-blueprint",
    response_model=BlueprintResponse
)
def generate_blueprint(
    project_id: int,
    db: Session = Depends(get_db)
):
    return BlueprintService.generate_blueprint(
        db,
        project_id
    )


@router.get(
    "/{project_id}/blueprint",
    response_model=BlueprintResponse
)
def get_blueprint(
    project_id: int,
    db: Session = Depends(get_db)
):
    return BlueprintService.get_blueprint(
        db,
        project_id
    )