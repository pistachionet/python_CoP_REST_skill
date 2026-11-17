"""Business rules for items. No HTTP and no database code — just the logic."""

from uuid import UUID, uuid4

from app.errors import ConflictError, NotFoundError
from app.repositories.item_repository import ItemRepository
from app.schemas.item import Item, ItemIn


class ItemService:
    def __init__(self, repository: ItemRepository) -> None:
        self.repository = repository

    def list_items(self) -> list[Item]:
        return self.repository.list()

    def get_item(self, item_id: UUID) -> Item:
        item = self.repository.get(item_id)
        if item is None:
            raise NotFoundError(f"Item {item_id} not found")
        return item

    def create_item(self, data: ItemIn) -> Item:
        self._ensure_name_is_free(data.name)
        return self.repository.save(Item(id=uuid4(), **data.model_dump()))

    def replace_item(self, item_id: UUID, data: ItemIn) -> Item:
        current = self.get_item(item_id)
        if data.name != current.name:
            self._ensure_name_is_free(data.name)
        return self.repository.save(Item(id=item_id, **data.model_dump()))

    def delete_item(self, item_id: UUID) -> None:
        self.get_item(item_id)
        self.repository.delete(item_id)

    def _ensure_name_is_free(self, name: str) -> None:
        if self.repository.get_by_name(name) is not None:
            raise ConflictError(f"An item named '{name}' already exists")
