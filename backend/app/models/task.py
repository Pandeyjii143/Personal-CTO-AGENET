from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Integer
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Task(TimestampMixin,Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id")
    )

    milestone_id: Mapped[int] = mapped_column(
        ForeignKey("milestones.id")
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        Text()
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending"
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        default="medium"
    )

    order_index: Mapped[int] = mapped_column(
        Integer
    )