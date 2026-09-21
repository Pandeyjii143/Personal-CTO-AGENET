from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:

    @staticmethod
    def create(
        db: Session,
        name: str,
        description: str,
        goal: str
    ):
        project = Project(
            name=name,
            description=description,
            goal=goal
        )
    

        db.add(project)
        db.commit()
        db.refresh(project)

        return project

    @staticmethod
    def get_all(db: Session):
        return db.query(Project).all()

    @staticmethod
    
    def get_by_id(
        db: Session,
        project_id: int
    ):
        return (
            db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )