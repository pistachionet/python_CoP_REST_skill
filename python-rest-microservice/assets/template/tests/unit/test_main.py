"""Unit tests for app-factory behaviour that depends on configuration."""

import pytest

from app.core.config import Settings
from app.main import create_app


@pytest.mark.parametrize(("environment", "docs_expected"), [("dev", True), ("prod", False)])
def test_docs_are_disabled_in_prod(environment: str, docs_expected: bool) -> None:
    app = create_app(Settings(environment=environment, log_json=False))

    assert (app.openapi_url is not None) is docs_expected
    assert (app.docs_url is not None) is docs_expected
