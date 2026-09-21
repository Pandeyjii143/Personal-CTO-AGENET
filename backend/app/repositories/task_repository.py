from sqlalchemy.orm import Session

from app.models.task import Task


class TaskRepository:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        milestone_id: int,
        title: str,
        description: str,
        priority: str,
        order_index: int
    ):
        task = Task(
            project_id=project_id,
            milestone_id=milestone_id,
            title=title,
            description=description,
            priority=priority,
            order_index=order_index
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return task

    @staticmethod
    def get_by_milestone(
        db: Session,
        milestone_id: int
    ):
        return (
            db.query(Task)
            .filter(
                Task.milestone_id == milestone_id
            )
            .order_by(
                Task.order_index
            )
            .all()
        )