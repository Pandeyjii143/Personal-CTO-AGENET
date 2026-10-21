import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def register_user(client: TestClient, email: str, password: str) -> None:
    response = client.post(
        "/auth/register",
        json={"email": email, "username": email, "password": password},
    )
    assert response.status_code in (200, 201), response.text


def login_user(client: TestClient, email: str, password: str) -> dict:
    # Support either JSON login payloads or OAuth2 password-form payloads.
    response = client.post(
        "/auth/login",
        json={"email": email, "username": email, "password": password},
    )
    if response.status_code == 422:
        response = client.post(
            "/auth/login",
            data={"username": email, "password": password},
        )
    assert response.status_code == 200, response.text
    return response.json()


def test_register_and_login_returns_access_and_refresh_tokens(client: TestClient):
    email = f"{uuid.uuid4().hex}@example.com"
    password = "Strong-test-password-123!"

    register_user(client, email, password)
    tokens = login_user(client, email, password)

    assert isinstance(tokens.get("access_token"), str)
    assert tokens["access_token"]
    assert isinstance(tokens.get("refresh_token"), str)
    assert tokens["refresh_token"]
    assert tokens.get("token_type", "bearer").lower() == "bearer"


def test_invalid_password_is_rejected(client: TestClient):
    email = f"{uuid.uuid4().hex}@example.com"
    register_user(client, email, "Strong-test-password-123!")

    response = client.post(
        "/auth/login",
        json={"email": email, "username": email, "password": "incorrect-password"},
    )
    if response.status_code == 422:
        response = client.post(
            "/auth/login",
            data={"username": email, "password": "incorrect-password"},
        )

    assert response.status_code in (401, 403)


def test_access_token_authenticates_user_and_refresh_issues_new_access_token(
    client: TestClient,
):
    email = f"{uuid.uuid4().hex}@example.com"
    password = "Strong-test-password-123!"
    register_user(client, email, password)
    tokens = login_user(client, email, password)

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200, me_response.text
    assert me_response.json().get("email") == email

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 200, refresh_response.text
    refreshed_tokens = refresh_response.json()
    assert isinstance(refreshed_tokens.get("access_token"), str)
    assert refreshed_tokens["access_token"]


def test_protected_endpoint_rejects_missing_or_invalid_access_token(
    client: TestClient,
):
    missing_token_response = client.get("/auth/me")
    assert missing_token_response.status_code in (401, 403)

    invalid_token_response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert invalid_token_response.status_code in (401, 403)
