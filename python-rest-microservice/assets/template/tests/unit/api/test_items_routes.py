"""Unit tests for the Item routes: HTTP contract (status codes, bodies, headers, errors)."""

import uuid
from decimal import Decimal

import httpx
import pytest
from fastapi import FastAPI

from app.api.deps import get_item_service
from app.models.item import Item
from tests.unit.fakes import FakeItemRepository

ITEMS = "/api/v1/items"


@pytest.fixture
async def existing(repository: FakeItemRepository) -> Item:
    return await repository.add(Item(name="Existing", price=Decimal("5.00")))


async def test_create_returns_201_with_location(client: httpx.AsyncClient) -> None:
    response = await client.post(ITEMS, json={"name": "Widget", "price": "9.99"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Widget"
    assert body["price"] == "9.99"
    assert response.headers["location"] == f"http://test{ITEMS}/{body['id']}"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"price": "1.00"}, id="missing-name"),
        pytest.param({"name": "", "price": "1.00"}, id="empty-name"),
        pytest.param({"name": "x", "price": "0"}, id="non-positive-price"),
        pytest.param({"name": "x", "price": "1.001"}, id="too-many-decimals"),
        pytest.param({"name": "x", "price": "1", "colour": "red"}, id="unknown-field"),
    ],
)
async def test_create_rejects_invalid_payload_as_problem_json(
    client: httpx.AsyncClient, payload: dict[str, str]
) -> None:
    response = await client.post(ITEMS, json=payload)

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Request Validation Failed"
    assert response.json()["errors"]


async def test_create_duplicate_name_returns_409(client: httpx.AsyncClient, existing: Item) -> None:
    response = await client.post(ITEMS, json={"name": existing.name, "price": "1.00"})

    assert response.status_code == 409
    assert response.json()["status"] == 409


async def test_get_returns_item(client: httpx.AsyncClient, existing: Item) -> None:
    response = await client.get(f"{ITEMS}/{existing.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(existing.id)


async def test_get_unknown_id_returns_404_problem_json(client: httpx.AsyncClient) -> None:
    item_id = uuid.uuid4()

    response = await client.get(f"{ITEMS}/{item_id}")

    assert response.status_code == 404
    assert response.json() == {
        "type": "about:blank",
        "title": "Resource Not Found",
        "status": 404,
        "detail": f"Item {item_id} was not found.",
        "instance": f"{ITEMS}/{item_id}",
    }


async def test_get_malformed_id_returns_422(client: httpx.AsyncClient) -> None:
    response = await client.get(f"{ITEMS}/not-a-uuid")

    assert response.status_code == 422


async def test_list_returns_page_envelope(client: httpx.AsyncClient, existing: Item) -> None:
    response = await client.get(ITEMS, params={"limit": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert [i["id"] for i in body["items"]] == [str(existing.id)]


async def test_list_rejects_limit_above_maximum(client: httpx.AsyncClient) -> None:
    response = await client.get(ITEMS, params={"limit": 101})

    assert response.status_code == 422


async def test_patch_updates_sent_fields_only(client: httpx.AsyncClient, existing: Item) -> None:
    response = await client.patch(f"{ITEMS}/{existing.id}", json={"price": "6.25"})

    assert response.status_code == 200
    assert response.json()["price"] == "6.25"
    assert response.json()["name"] == "Existing"


async def test_patch_rejects_explicit_null_for_required_field(
    client: httpx.AsyncClient, existing: Item
) -> None:
    response = await client.patch(f"{ITEMS}/{existing.id}", json={"name": None})

    assert response.status_code == 422


async def test_delete_returns_204(
    client: httpx.AsyncClient, existing: Item, repository: FakeItemRepository
) -> None:
    response = await client.delete(f"{ITEMS}/{existing.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert existing.id not in repository.items


async def test_unknown_route_returns_404_problem_json(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/nope")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"


async def test_unhandled_error_returns_500_without_leaking_details(
    app: FastAPI, client: httpx.AsyncClient
) -> None:
    def broken_service() -> None:
        raise RuntimeError("secret connection string in message")

    app.dependency_overrides[get_item_service] = broken_service

    response = await client.get(ITEMS)

    assert response.status_code == 500
    assert response.json()["title"] == "Internal Server Error"
    assert "secret" not in response.text
