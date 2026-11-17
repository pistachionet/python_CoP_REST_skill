"""API-layer unit fixtures: the real app and routing, with the service wired to an in-memory
fake. The lifespan is NOT run, so no engine or database is ever created."""

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from app.api.deps import get_item_service
from app.core.config import Settings
from app.main import create_app
from app.services.item import ItemService
from tests.unit.fakes import FakeItemRepository


@pytest.fixture
def repository() -> FakeItemRepository:
    return FakeItemRepository()


@pytest.fixture
def app(settings: Settings, repository: FakeItemRepository) -> FastAPI:
    app = create_app(settings)
    app.dependency_overrides[get_item_service] = lambda: ItemService(repository)
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
