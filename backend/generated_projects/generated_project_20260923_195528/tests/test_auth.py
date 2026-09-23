import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def register_user(client: TestClient, email: str, password: str = "StrongPassword123!"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )


def test_register_and_login_returns_access_token(client: TestClient):
    email = f"{uuid.uuid4().hex}@example.com"
    password = "StrongPassword123!"

    response = register_user(client, email, password)
    assert response.status_code in (200, 201), response.text

    login_response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text

    payload = login_response.json()
    assert isinstance(payload.get("access_token"), str)
    assert payload["access_token"]
    assert payload.get("token_type", "bearer").lower() == "bearer"


def test_authenticated_user_can_access_current_user_endpoint(client: TestClient):
    email = f"{uuid.uuid4().hex}@example.com"
    password = "StrongPassword123!"

    registration = register_user(client, email, password)
    assert registration.status_code in (200, 201), registration.text

    login_response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json().get("email") == email


def test_current_user_endpoint_rejects_missing_token(client: TestClient):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_current_user_endpoint_rejects_invalid_token(client: TestClient):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert response.status_code == 401


def test_login_rejects_incorrect_password(client: TestClient):
    email = f"{uuid.uuid4().hex}@example.com"
    registration = register_user(client, email)
    assert registration.status_code in (200, 201), registration.text

    response = client.post(
        "/auth/login",
        data={"username": email, "password": "WrongPassword123!"},
    )
    assert response.status_code == 401


def test_registration_rejects_duplicate_email(client: TestClient):
    email = f"{uuid.uuid4().hex}@example.com"
    first_response = register_user(client, email)
    assert first_response.status_code in (200, 201), first_response.text

    duplicate_response = register_user(client, email)
    assert duplicate_response.status_code in (400, 409, 422)
