from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import mapped_column


class TimestampMixin:

    created_at = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )