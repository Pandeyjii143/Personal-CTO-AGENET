import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import models  # noqa: F401 — ensure model tables are registered with Base


@pytest.fixture
def client():
    """Provide a client backed by a fresh in-memory database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def credentials():
    suffix = uuid.uuid4().hex
    return {
        "email": f"user-{suffix}@example.com",
        "password": "Correct-Horse-Battery-42!",
    }


def register_user(client: TestClient, user_credentials: dict) -> None:
    response = client.post("/auth/register", json=user_credentials)
    assert response.status_code in (200, 201), response.text


def test_register_creates_user_without_returning_password(client: TestClient):
    user_credentials = credentials()

    response = client.post("/auth/register", json=user_credentials)

    assert response.status_code in (200, 201), response.text
    body = response.json()
    assert body["email"] == user_credentials["email"]
    assert "password" not in body
    assert "hashed_password" not in body


def test_duplicate_registration_is_rejected(client: TestClient):
    user_credentials = credentials()
    register_user(client, user_credentials)

    response = client.post("/auth/register", json=user_credentials)

    assert response.status_code in (400, 409), response.text


def test_login_returns_bearer_token_for_valid_credentials(client: TestClient):
    user_credentials = credentials()
    register_user(client, user_credentials)

    response = client.post("/auth/login", json=user_credentials)

    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body.get("access_token"), str)
    assert body["access_token"]
    assert body.get("token_type", "bearer").lower() == "bearer"


def test_login_rejects_invalid_password(client: TestClient):
    user_credentials = credentials()
    register_user(client, user_credentials)

    response = client.post(
        "/auth/login",
        json={"email": user_credentials["email"], "password": "incorrect-password"},
    )

    assert response.status_code in (400, 401), response.text


def test_current_user_requires_authentication(client: TestClient):
    response = client.get("/auth/me")

    assert response.status_code in (401, 403), response.text


def test_current_user_is_returned_for_valid_token(client: TestClient):
    user_credentials = credentials()
    register_user(client, user_credentials)
    login_response = client.post("/auth/login", json=user_credentials)
    assert login_response.status_code == 200, login_response.text

    token = login_response.json()["access_token"]
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email"] == user_credentials["email"]
    assert "password" not in body
    assert "hashed_password" not in body


def test_current_user_rejects_malformed_token(client: TestClient):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )

    assert response.status_code in (401, 403), response.text
