import importlib
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")


def _load_database_components():
    for module_name in ("app.db.session", "app.core.database", "app.database"):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue

        get_db = getattr(module, "get_db", None)
        base = getattr(module, "Base", None)
        if get_db is not None and base is not None:
            return get_db, base

    raise ImportError(
        "Could not find get_db and Base; expected them in app.db.session, "
        "app.core.database, or app.database."
    )


get_db, Base = _load_database_components()

# Import model modules so their tables are registered in Base.metadata.
for _module_name in ("app.models", "app.models.user"):
    try:
        importlib.import_module(_module_name)
    except ModuleNotFoundError as exc:
        if exc.name != _module_name:
            raise

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
