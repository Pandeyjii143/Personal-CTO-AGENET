from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def expense_payload(**overrides):
    payload = {
        "description": f"Test expense {uuid4()}",
        "amount": 12.50,
        "category": "Food",
        "date": date.today().isoformat(),
    }
    payload.update(overrides)
    return payload


def test_create_and_list_expenses(client):
    payload = expense_payload()

    create_response = client.post("/expenses", json=payload)
    assert create_response.status_code in (200, 201)
    created = create_response.json()
    assert created["description"] == payload["description"]
    assert float(created["amount"]) == pytest.approx(payload["amount"])
    assert created["category"] == payload["category"]
    assert created["date"] == payload["date"]
    assert "id" in created

    list_response = client.get("/expenses")
    assert list_response.status_code == 200
    expenses = list_response.json()
    if isinstance(expenses, dict):
        expenses = expenses.get("expenses", [])
    assert any(expense["id"] == created["id"] for expense in expenses)


def test_update_expense(client):
    create_response = client.post("/expenses", json=expense_payload())
    assert create_response.status_code in (200, 201)
    expense_id = create_response.json()["id"]

    updated_payload = expense_payload(
        description=f"Updated expense {uuid4()}",
        amount=24.75,
        category="Transport",
    )
    response = client.put(f"/expenses/{expense_id}", json=updated_payload)

    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == expense_id
    assert updated["description"] == updated_payload["description"]
    assert float(updated["amount"]) == pytest.approx(updated_payload["amount"])
    assert updated["category"] == updated_payload["category"]
    assert updated["date"] == updated_payload["date"]


def test_delete_expense(client):
    create_response = client.post("/expenses", json=expense_payload())
    assert create_response.status_code in (200, 201)
    expense_id = create_response.json()["id"]

    delete_response = client.delete(f"/expenses/{expense_id}")
    assert delete_response.status_code in (200, 204)

    list_response = client.get("/expenses")
    assert list_response.status_code == 200
    expenses = list_response.json()
    if isinstance(expenses, dict):
        expenses = expenses.get("expenses", [])
    assert all(expense["id"] != expense_id for expense in expenses)


def test_amount_must_be_positive(client):
    for amount in (0, -1):
        response = client.post(
            "/expenses",
            json=expense_payload(amount=amount),
        )
        assert 400 <= response.status_code < 500


def test_home_page_returns_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
