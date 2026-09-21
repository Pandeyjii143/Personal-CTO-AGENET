from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Milestone(TimestampMixin,Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id")
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

    order_index: Mapped[int] = mapped_column(
        Integer
    )