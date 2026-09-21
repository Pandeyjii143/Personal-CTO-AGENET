from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from datetime import datetime
from sqlalchemy import DateTime
from app.models.mixins import TimestampMixin

class Project(TimestampMixin,Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255))

    description: Mapped[str] = mapped_column(Text())

    goal: Mapped[str] = mapped_column(Text())

    status: Mapped[str] = mapped_column(
        String(50),
        default="planning"
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
