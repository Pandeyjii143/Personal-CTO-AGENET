from sqlalchemy.orm import Session

from app.models.blueprint import Blueprint


class BlueprintRepository:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        architecture: dict,
        tech_stack: list,
        risks: list
    ):
        blueprint = Blueprint(
            project_id=project_id,
            architecture=architecture,
            tech_stack=tech_stack,
            risks=risks
        )

        db.add(blueprint)
        db.commit()
        db.refresh(blueprint)

        return blueprint

    @staticmethod
    def get_by_project_id(
        db: Session,
        project_id: int
    ):
        return (
            db.query(Blueprint)
            .filter(Blueprint.project_id == project_id)
            .first()
        )