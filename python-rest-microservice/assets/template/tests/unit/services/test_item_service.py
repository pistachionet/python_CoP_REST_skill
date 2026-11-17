"""Unit tests for ItemService: business rules only, no I/O (in-memory fake repository)."""

import uuid
from decimal import Decimal

import pytest

from app.core.errors import ConflictError, NotFoundError
from app.models.item import Item
from app.schemas.item import ItemUpdate
from app.services.item import ItemService
from tests.factories import ItemCreateFactory
from tests.unit.fakes import FakeItemRepository


@pytest.fixture
def repository() -> FakeItemRepository:
    return FakeItemRepository()


@pytest.fixture
def service(repository: FakeItemRepository) -> ItemService:
    return ItemService(repository)


@pytest.fixture
async def existing(repository: FakeItemRepository) -> Item:
    return await repository.add(Item(name="Existing", price=Decimal("5.00")))


class TestCreate:
    async def test_persists_and_returns_item(
        self, service: ItemService, repository: FakeItemRepository
    ) -> None:
        data = ItemCreateFactory.build(name="Widget")

        item = await service.create(data)

        assert item.name == "Widget"
        assert repository.items[item.id] is item

    async def test_rejects_duplicate_name(self, service: ItemService, existing: Item) -> None:
        with pytest.raises(ConflictError, match="already exists"):
            await service.create(ItemCreateFactory.build(name=existing.name))


class TestGet:
    async def test_returns_existing_item(self, service: ItemService, existing: Item) -> None:
        assert await service.get(existing.id) is existing

    async def test_raises_not_found_for_unknown_id(self, service: ItemService) -> None:
        with pytest.raises(NotFoundError):
            await service.get(uuid.uuid4())


class TestList:
    async def test_applies_limit_and_offset(
        self, service: ItemService, repository: FakeItemRepository
    ) -> None:
        for n in range(3):
            await repository.add(Item(name=f"item-{n}", price=Decimal(1)))

        page, total = await service.list(limit=2, offset=1)

        assert total == 3
        assert [i.name for i in page] == ["item-1", "item-2"]


class TestUpdate:
    async def test_changes_only_fields_that_were_sent(
        self, service: ItemService, existing: Item
    ) -> None:
        updated = await service.update(existing.id, ItemUpdate(price=Decimal("7.50")))

        assert updated.price == Decimal("7.50")
        assert updated.name == "Existing"

    async def test_allows_keeping_the_same_name(self, service: ItemService, existing: Item) -> None:
        updated = await service.update(existing.id, ItemUpdate(name=existing.name))

        assert updated.name == existing.name

    async def test_rejects_rename_to_a_taken_name(
        self, service: ItemService, repository: FakeItemRepository, existing: Item
    ) -> None:
        other = await repository.add(Item(name="Other", price=Decimal(1)))

        with pytest.raises(ConflictError):
            await service.update(other.id, ItemUpdate(name=existing.name))

    async def test_raises_not_found_for_unknown_id(self, service: ItemService) -> None:
        with pytest.raises(NotFoundError):
            await service.update(uuid.uuid4(), ItemUpdate(name="x"))


class TestDelete:
    async def test_removes_item(
        self, service: ItemService, repository: FakeItemRepository, existing: Item
    ) -> None:
        await service.delete(existing.id)

        assert existing.id not in repository.items

    async def test_raises_not_found_for_unknown_id(self, service: ItemService) -> None:
        with pytest.raises(NotFoundError):
            await service.delete(uuid.uuid4())
