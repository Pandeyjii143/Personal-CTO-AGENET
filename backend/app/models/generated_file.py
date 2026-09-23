# app/models/generated_file.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime
)

from sqlalchemy.sql import func

from app.db.base import Base


class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id = Column(Integer, primary_key=True)

    generated_project_id = Column(
        Integer,
        ForeignKey("generated_projects.id"),
        nullable=False
    )

    file_path = Column(
        String,
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )