"""Unit tests for the JSON log formatter."""

import json
import logging

from app.core.logging import JsonFormatter


def _record(**extra: object) -> logging.LogRecord:
    record = logging.makeLogRecord({"name": "app.test", "levelname": "INFO", "msg": "hello %s"})
    record.args = ("world",)
    record.__dict__.update(extra)
    return record


def test_emits_one_json_object_with_standard_fields() -> None:
    payload = json.loads(JsonFormatter("svc").format(_record()))

    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["service"] == "svc"
    assert "timestamp" in payload


def test_includes_extra_fields() -> None:
    payload = json.loads(JsonFormatter("svc").format(_record(order_id="123")))

    assert payload["order_id"] == "123"
