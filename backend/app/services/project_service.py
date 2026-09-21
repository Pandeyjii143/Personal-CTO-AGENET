from sqlalchemy.orm import Session

from app.repositories.project_repository import (
    ProjectRepository
)


class ProjectService:

    @staticmethod
    def create_project(
        db: Session,
        name: str,
        description: str,
        goal: str
    ):
        return ProjectRepository.create(
            db=db,
            name=name,
            description=description,
            goal=goal
        )

    @staticmethod
    def get_projects(
        db: Session
    ):
        return ProjectRepository.get_all(db)
    
    @staticmethod
    def get_project(
        db: Session,
        project_id: int
    ):
        return ProjectRepository.get_by_id(
            db,
            project_id
        )