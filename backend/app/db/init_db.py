from app.db.base import Base
from app.db.session import engine

import app.models


def create_tables():
    Base.metadata.create_all(bind=engine)