from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def new_user() -> dict[str, str]:
    return {
        "email": f"{uuid4().hex}@example.com",
        "password": "Strong-password-123!",
    }


def register_user(client: TestClient, user: dict[str, str]) -> None:
    response = client.post("/auth/register", json=user)
    assert response.status_code in (200, 201), response.text


def test_register_login_and_access_protected_endpoint(client: TestClient) -> None:
    user = new_user()
    register_user(client, user)

    login_response = client.post("/auth/login", json=user)
    assert login_response.status_code == 200, login_response.text

    token_data = login_response.json()
    access_token = token_data["access_token"]
    assert isinstance(access_token, str)
    assert len(access_token.split(".")) == 3
    assert token_data.get("token_type", "bearer").lower() == "bearer"

    me_response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["email"] == user["email"]


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    user = new_user()
    register_user(client, user)

    response = client.post("/auth/register", json=user)
    assert response.status_code in (400, 409, 422), response.text


def test_login_rejects_invalid_password(client: TestClient) -> None:
    user = new_user()
    register_user(client, user)

    response = client.post(
        "/auth/login",
        json={"email": user["email"], "password": "incorrect-password"},
    )
    assert response.status_code in (400, 401, 403), response.text


def test_protected_endpoint_rejects_missing_or_invalid_token(
    client: TestClient,
) -> None:
    missing_token_response = client.get("/auth/me")
    assert missing_token_response.status_code in (401, 403)

    invalid_token_response = client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid.token.value"}
    )
    assert invalid_token_response.status_code in (401, 403)
