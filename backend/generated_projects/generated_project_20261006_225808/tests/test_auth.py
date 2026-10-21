import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def create_user(client: TestClient) -> dict[str, str]:
    email = f"{uuid.uuid4().hex}@example.com"
    password = "Strong-test-password-123!"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code in (200, 201), response.text
    return {"email": email, "password": password}


def login(client: TestClient, email: str, password: str):
    return client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )


def test_register_and_login_returns_access_token(client: TestClient):
    user = create_user(client)

    response = login(client, user["email"], user["password"])

    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body.get("access_token"), str)
    assert body["access_token"]
    assert body.get("token_type", "bearer").lower() == "bearer"


def test_register_rejects_duplicate_email(client: TestClient):
    user = create_user(client)

    response = client.post(
        "/auth/register",
        json={"email": user["email"], "password": user["password"]},
    )

    assert response.status_code in (400, 409), response.text


def test_login_rejects_incorrect_password(client: TestClient):
    user = create_user(client)

    response = login(client, user["email"], "incorrect-password")

    assert response.status_code == 401, response.text


def test_protected_profile_requires_authentication(client: TestClient):
    response = client.get("/auth/me")

    assert response.status_code == 401, response.text


def test_authenticated_user_can_access_profile(client: TestClient):
    user = create_user(client)
    token_response = login(client, user["email"], user["password"])
    assert token_response.status_code == 200, token_response.text
    token = token_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["email"] == user["email"]


def test_protected_profile_rejects_invalid_token(client: TestClient):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401, response.text
