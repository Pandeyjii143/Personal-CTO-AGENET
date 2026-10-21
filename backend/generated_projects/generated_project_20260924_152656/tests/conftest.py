import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def test_engine():
    """Create a database engine shared by the test session."""
    database_url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    engine_options = {}

    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if database_url.endswith(":memory:"):
            engine_options["poolclass"] = StaticPool

    engine = create_engine(database_url, **engine_options)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Provide an isolated database session for a test."""
    Base.metadata.create_all(bind=test_engine)
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    session = testing_session()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    """Provide a FastAPI test client using the test database."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
