import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")

_engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite:"):
    _engine_options["connect_args"] = {"check_same_thread": False}
    if DATABASE_URL in {"sqlite://", "sqlite:///:memory:"}:
        _engine_options["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **_engine_options)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for application database models."""


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and ensure it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
