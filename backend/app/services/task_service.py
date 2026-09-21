from sqlalchemy.orm import Session

from app.agents.task_agent import TaskAgent
from app.repositories.task_repository import (
    TaskRepository
)
from app.repositories.milestone_repository import (
    MilestoneRepository

)
from fastapi import HTTPException

class TaskService:

    @staticmethod
    def generate_tasks(
        db: Session,
        milestone_id: int
    ):

        existing = TaskRepository.get_by_milestone(
            db,
            milestone_id
        )

        if existing:
            return existing


        milestone = (
            db.query(
                __import__(
                    "app.models.milestone",
                    fromlist=["Milestone"]
                ).Milestone
            )
            .filter_by(id=milestone_id)
            .first()
        )
        if not milestone:
          raise HTTPException(
              status_code=404,
              detail="Milestone not found"
          )

        tasks = TaskAgent.generate(
            milestone.title
        )

        result = []

        for index, task in enumerate(
            tasks,
            start=1
        ):
            saved = TaskRepository.create(
                db=db,
                project_id=milestone.project_id,
                milestone_id=milestone_id,
                title=task["title"],
                description=task["description"],
                priority=task["priority"],
                order_index=index
            )

            result.append(saved)

        return result

    @staticmethod
    def get_tasks(
        db: Session,
        milestone_id: int
    ):
        milestone = MilestoneRepository. get_by_project_id(
            db,
            milestone_id
        )

        if not milestone:
            raise HTTPException(
                status_code=404,
                detail="Milestone not found"
            )

        return TaskRepository.get_by_milestone(
            db,
            milestone_id
        )