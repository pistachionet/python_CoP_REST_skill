"""Fixtures shared by unit and integration tests."""

import pytest

from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test", log_json=False, log_level="WARNING")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Everything under tests/integration/ is automatically marked ``integration``."""
    for item in items:
        if "integration" in item.path.relative_to(item.config.rootpath).parts:
            item.add_marker(pytest.mark.integration)
