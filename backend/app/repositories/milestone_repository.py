from sqlalchemy.orm import Session

from app.models.milestone import Milestone


class MilestoneRepository:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        title: str,
        description: str,
        order_index: int
    ):
        milestone = Milestone(
            project_id=project_id,
            title=title,
            description=description,
            order_index=order_index
        )

        db.add(milestone)
        db.commit()
        db.refresh(milestone)

        return milestone

    @staticmethod
    def get_by_project_id(
        db: Session,
        project_id: int
    ):
        return (
            db.query(Milestone)
            .filter(
                Milestone.project_id == project_id
            )
            .order_by(
                Milestone.order_index
            )
            .all()
        )