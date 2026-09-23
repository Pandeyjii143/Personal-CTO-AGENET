from sqlalchemy.orm import Session

from app.repositories.project_repository import (
    ProjectRepository
)

from fastapi import HTTPException

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
    def get_projects(db):
        return ProjectRepository.get_all(db)

    @staticmethod
    def get_project(
        db: Session,
        project_id: int
    ):
        project = ProjectRepository.get_by_id(
            db,
            project_id
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        return project
    
    @staticmethod
    def update_project(
        db: Session,
        project_id: int,
        update_data: dict
    ):
        project = ProjectRepository.get_by_id(
            db,
            project_id
        )

        if not project:
          raise HTTPException(
              status_code=404,
              detail="Project not found"
    )

        return ProjectRepository.update(
            db,
            project,
            update_data
        )
    @staticmethod
    def delete_project(
        db: Session,
        project_id: int
    ):
        project = ProjectRepository.get_by_id(
            db,
            project_id
        )
        if not project:
            raise HTTPException(
            status_code=404,
            detail="Project not found"
                    )

       

        ProjectRepository.delete(
            db,
            project
        )

        return True