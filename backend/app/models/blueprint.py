from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Blueprint(TimestampMixin,Base):
    __tablename__ = "blueprints"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id")
    )

    architecture: Mapped[dict] = mapped_column(
        JSON,
        default=dict
    )

    tech_stack: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    risks: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="generated"
    )