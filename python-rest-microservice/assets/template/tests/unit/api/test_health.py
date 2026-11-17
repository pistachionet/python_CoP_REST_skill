"""Unit tests for health probes. The engine is replaced by a stub, so no database is used."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI


class _UnreachableEngine:
    @asynccontextmanager
    async def connect(self) -> AsyncIterator[Any]:
        raise ConnectionRefusedError("database is down")
        yield  # pragma: no cover


async def test_live_is_ok_without_checking_dependencies(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_returns_503_when_database_unreachable(
    app: FastAPI, client: httpx.AsyncClient
) -> None:
    app.state.engine = _UnreachableEngine()

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["checks"] == {"database": "down"}
