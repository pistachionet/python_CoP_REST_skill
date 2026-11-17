"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    """A fresh app per test, so no data leaks from one test to another."""
    return TestClient(create_app())
