"""Integration tests: HTTP → service → repository → PostgreSQL, through the real app."""

import asyncio
import uuid

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

ITEMS = "/api/v1/items"


async def _create(client: httpx.AsyncClient, name: str, price: str = "1.00") -> dict[str, str]:
    response = await client.post(ITEMS, json={"name": name, "price": price})
    assert response.status_code == 201, response.text
    body: dict[str, str] = response.json()
    return body


async def test_crud_lifecycle(client: httpx.AsyncClient) -> None:
    created = await _create(client, "Widget", "9.99")
    url = f"{ITEMS}/{created['id']}"

    fetched = await client.get(url)
    assert fetched.status_code == 200
    assert fetched.json() == created

    patched = await client.patch(url, json={"description": "Now with more widget"})
    assert patched.status_code == 200
    assert patched.json()["description"] == "Now with more widget"
    assert patched.json()["updated_at"] >= created["updated_at"]

    assert (await client.delete(url)).status_code == 204
    assert (await client.get(url)).status_code == 404


async def test_create_is_committed_to_the_database(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    created = await _create(client, "Persisted", "2.50")

    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT name, price FROM items WHERE id = :id"),
                {"id": uuid.UUID(created["id"])},
            )
        ).one()

    assert row.name == "Persisted"
    assert str(row.price) == "2.50"


async def test_duplicate_name_returns_409(client: httpx.AsyncClient) -> None:
    await _create(client, "Unique")

    response = await client.post(ITEMS, json={"name": "Unique", "price": "1.00"})

    assert response.status_code == 409
    assert response.headers["content-type"] == "application/problem+json"


async def test_list_paginates_in_creation_order(client: httpx.AsyncClient) -> None:
    for name in ["first", "second", "third"]:
        await _create(client, name)
        await asyncio.sleep(0.01)  # distinct created_at values

    response = await client.get(ITEMS, params={"limit": 2, "offset": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert [i["name"] for i in body["items"]] == ["second", "third"]


async def test_unknown_id_returns_404(client: httpx.AsyncClient) -> None:
    for method in ("GET", "PATCH", "DELETE"):
        response = await client.request(method, f"{ITEMS}/{uuid.uuid4()}", json={})
        assert response.status_code == 404, method


async def test_readiness_reports_database_up(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["checks"] == {"database": "up"}
