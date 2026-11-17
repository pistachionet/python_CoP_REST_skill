"""In-memory fakes. Prefer a fake that honours the interface over ad-hoc mocks: tests stay
readable and break loudly if the interface changes (mypy checks the Protocol)."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from app.models.item import Item
from app.repositories.item import ItemRepository


class FakeItemRepository:
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Item] = {}

    async def get(self, item_id: uuid.UUID) -> Item | None:
        return self.items.get(item_id)

    async def get_by_name(self, name: str) -> Item | None:
        return next((i for i in self.items.values() if i.name == name), None)

    async def list(self, *, limit: int, offset: int) -> tuple[Sequence[Item], int]:
        ordered = sorted(self.items.values(), key=lambda i: (i.created_at, i.id))
        return ordered[offset : offset + limit], len(ordered)

    async def add(self, item: Item) -> Item:
        self._stamp(item)
        self.items[item.id] = item
        return item

    async def save(self, item: Item) -> Item:
        item.updated_at = datetime.now(UTC)
        return item

    async def delete(self, item: Item) -> None:
        del self.items[item.id]

    @staticmethod
    def _stamp(item: Item) -> None:
        # Mimic what the database does on INSERT.
        now = datetime.now(UTC)
        item.id = item.id or uuid.uuid4()
        item.created_at = item.created_at or now
        item.updated_at = item.updated_at or now


# Static check: the fake must satisfy the same Protocol the service depends on.
_: type[ItemRepository] = FakeItemRepository
