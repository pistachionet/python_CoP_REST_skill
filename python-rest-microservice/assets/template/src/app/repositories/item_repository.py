"""Data access for items.

``ItemRepository`` is the interface the service depends on. ``InMemoryItemRepository`` is a
placeholder implementation: replace it with one for the client's chosen data store
(PostgreSQL, SQL Server, DynamoDB, Cosmos DB, ...) without changing the service or the API.
"""

from typing import Protocol
from uuid import UUID

from app.schemas.item import Item


class ItemRepository(Protocol):
    def list(self) -> list[Item]: ...
    def get(self, item_id: UUID) -> Item | None: ...
    def get_by_name(self, name: str) -> Item | None: ...
    def save(self, item: Item) -> Item: ...
    def delete(self, item_id: UUID) -> None: ...


class InMemoryItemRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, Item] = {}

    def list(self) -> list[Item]:
        return list(self._items.values())

    def get(self, item_id: UUID) -> Item | None:
        return self._items.get(item_id)

    def get_by_name(self, name: str) -> Item | None:
        return next((item for item in self._items.values() if item.name == name), None)

    def save(self, item: Item) -> Item:
        self._items[item.id] = item
        return item

    def delete(self, item_id: UUID) -> None:
        self._items.pop(item_id, None)
