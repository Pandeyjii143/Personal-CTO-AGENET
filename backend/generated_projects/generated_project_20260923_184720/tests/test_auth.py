import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def new_user_payload():
    unique_id = uuid.uuid4().hex
    return {
        "username": f"user_{unique_id}",
        "email": f"{unique_id}@example.com",
        "password": "StrongTestPassword!123",
    }


def test_register_creates_user_without_exposing_password(client):
    payload = new_user_payload()

    response = client.post("/auth/register", json=payload)

    assert response.status_code in (200, 201)
    body = response.json()
    assert body.get("email") == payload["email"] or body.get("user", {}).get("email") == payload["email"]
    assert "password" not in body
    assert "password_hash" not in body
    assert payload["password"] not in response.text


def test_register_rejects_duplicate_email(client):
    payload = new_user_payload()

    first_response = client.post("/auth/register", json=payload)
    assert first_response.status_code in (200, 201)

    duplicate_response = client.post("/auth/register", json=payload)
    assert duplicate_response.status_code == 400


def test_login_returns_bearer_token_and_allows_access_to_current_user(client):
    payload = new_user_payload()
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code in (200, 201)

    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    assert login_response.status_code == 200
    token_data = login_response.json()
    assert token_data.get("access_token")
    assert token_data.get("token_type", "bearer").lower() == "bearer"
    assert len(token_data["access_token"].split(".")) == 3

    current_user_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert current_user_response.status_code == 200
    assert current_user_response.json().get("email") == payload["email"]


def test_login_rejects_incorrect_password(client):
    payload = new_user_payload()
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code in (200, 201)

    response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "incorrect-password"},
    )

    assert response.status_code == 401


def test_current_user_requires_valid_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code in (401, 403)
