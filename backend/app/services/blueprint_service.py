from sqlalchemy.orm import Session

from app.repositories.blueprint_repository import BlueprintRepository
from app.repositories.project_repository import ProjectRepository
from app.agents.architect_agent import ArchitectAgent
from fastapi import HTTPException


class BlueprintService:

    @staticmethod
    def generate_blueprint(
        db: Session,
        project_id: int
    ):
        existing = BlueprintRepository.get_by_project_id(
            db,
            project_id
        )

        if existing:
            return existing

        

        project = ProjectRepository.get_by_id(
            db,
            project_id
        )
        if not project:
          raise HTTPException(
              status_code=404,
              detail="Project not found"
          )

        result = ArchitectAgent.generate(
            project_name=project.name,
            goal=project.goal
        )

        

        return BlueprintRepository.create(
            db=db,
            project_id=project_id,
            architecture=result["architecture"],
            tech_stack=result["tech_stack"],
            risks=result["risks"]
        )

    @staticmethod
    def get_blueprint(
        db: Session,
        project_id: int
    ):
        blueprint = BlueprintRepository.get_by_project_id(
            db,
            project_id
        )

        if not blueprint:
            raise HTTPException(
                status_code=404,
                detail="Blueprint not found"
            )

        return blueprint