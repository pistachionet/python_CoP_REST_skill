"""Unit tests: call the service directly. No HTTP, no external systems."""

from uuid import uuid4

import pytest

from app.errors import ConflictError, NotFoundError
from app.repositories.item_repository import InMemoryItemRepository
from app.schemas.item import ItemIn
from app.services.item_service import ItemService


@pytest.fixture
def service() -> ItemService:
    return ItemService(InMemoryItemRepository())


def test_create_item_assigns_an_id(service: ItemService) -> None:
    item = service.create_item(ItemIn(name="Widget"))

    assert item.id is not None
    assert service.get_item(item.id) == item


def test_create_item_rejects_duplicate_name(service: ItemService) -> None:
    service.create_item(ItemIn(name="Widget"))

    with pytest.raises(ConflictError):
        service.create_item(ItemIn(name="Widget"))


def test_get_item_raises_not_found_for_unknown_id(service: ItemService) -> None:
    with pytest.raises(NotFoundError):
        service.get_item(uuid4())


def test_replace_item_keeps_the_same_id(service: ItemService) -> None:
    item = service.create_item(ItemIn(name="Widget", quantity=1))

    replaced = service.replace_item(item.id, ItemIn(name="Widget", quantity=5))

    assert replaced.id == item.id
    assert replaced.quantity == 5


def test_replace_item_rejects_renaming_to_a_taken_name(service: ItemService) -> None:
    service.create_item(ItemIn(name="Widget"))
    gadget = service.create_item(ItemIn(name="Gadget"))

    with pytest.raises(ConflictError):
        service.replace_item(gadget.id, ItemIn(name="Widget"))


def test_delete_item_removes_it(service: ItemService) -> None:
    item = service.create_item(ItemIn(name="Widget"))

    service.delete_item(item.id)

    with pytest.raises(NotFoundError):
        service.get_item(item.id)


def test_delete_item_raises_not_found_for_unknown_id(service: ItemService) -> None:
    with pytest.raises(NotFoundError):
        service.delete_item(uuid4())
