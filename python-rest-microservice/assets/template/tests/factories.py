"""Test-data factories. Build valid payloads; override only the fields a test cares about."""

from polyfactory.factories.pydantic_factory import ModelFactory

from app.schemas.item import ItemCreate


class ItemCreateFactory(ModelFactory[ItemCreate]):
    __check_model__ = True
