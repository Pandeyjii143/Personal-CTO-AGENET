# app/models/generated_project.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class GeneratedProject(Base):
    __tablename__ = "generated_projects"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    name = Column(String, nullable=False)

    status = Column(
        String,
        default="generated"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )