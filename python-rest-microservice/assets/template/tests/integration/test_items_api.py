"""Integration tests: send real HTTP requests through the whole app (routes -> service ->
repository). Once the service uses a real data store, these run against a test instance of it."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

ITEMS = "/api/v1/items"


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_then_get_item(client: TestClient) -> None:
    created = client.post(ITEMS, json={"name": "Widget", "quantity": 3})

    assert created.status_code == 201
    item_id = created.json()["id"]

    fetched = client.get(f"{ITEMS}/{item_id}")
    assert fetched.status_code == 200
    assert fetched.json() == {"id": item_id, "name": "Widget", "description": None, "quantity": 3}


def test_list_items(client: TestClient) -> None:
    client.post(ITEMS, json={"name": "Widget"})
    client.post(ITEMS, json={"name": "Gadget"})

    response = client.get(ITEMS)

    assert response.status_code == 200
    assert sorted(item["name"] for item in response.json()) == ["Gadget", "Widget"]


def test_replace_item(client: TestClient) -> None:
    item_id = client.post(ITEMS, json={"name": "Widget"}).json()["id"]

    response = client.put(f"{ITEMS}/{item_id}", json={"name": "Widget", "quantity": 9})

    assert response.status_code == 200
    assert response.json()["quantity"] == 9


def test_delete_item(client: TestClient) -> None:
    item_id = client.post(ITEMS, json={"name": "Widget"}).json()["id"]

    assert client.delete(f"{ITEMS}/{item_id}").status_code == 204
    assert client.get(f"{ITEMS}/{item_id}").status_code == 404


def test_duplicate_name_returns_409(client: TestClient) -> None:
    client.post(ITEMS, json={"name": "Widget"})

    response = client.post(ITEMS, json={"name": "Widget"})

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_unknown_item_returns_404(client: TestClient) -> None:
    response = client.get(f"{ITEMS}/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "body",
    [
        {},                                   # name missing
        {"name": ""},                         # name empty
        {"name": "Widget", "quantity": -1},   # quantity negative
    ],
)
def test_invalid_body_returns_422(client: TestClient, body: dict[str, object]) -> None:
    response = client.post(ITEMS, json=body)

    assert response.status_code == 422
