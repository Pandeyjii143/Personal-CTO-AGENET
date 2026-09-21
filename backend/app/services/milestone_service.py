from sqlalchemy.orm import Session

from app.agents.planner_agent import PlannerAgent
from app.repositories.project_repository import ProjectRepository
from app.repositories.milestone_repository import (
    MilestoneRepository
)
from fastapi import HTTPException

class MilestoneService:

    @staticmethod
    def generate_milestones(
        db: Session,
        project_id: int
    ):

        existing = MilestoneRepository.get_by_project_id(
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

        milestones = PlannerAgent.generate(
            project_name=project.name,
            goal=project.goal
        )

        result = []

        for index, milestone in enumerate(
            milestones,
            start=1
        ):
            saved = MilestoneRepository.create(
                db=db,
                project_id=project_id,
                title=milestone["title"],
                description=milestone["description"],
                order_index=index
            )

            result.append(saved)

        return result

    @staticmethod
    def get_milestones(
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

        milestones = MilestoneRepository.get_by_project_id(
            db,
            project_id
        )

        return milestones