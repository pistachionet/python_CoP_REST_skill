"""Business logic for ``Item``. No FastAPI, no SQL — only rules and orchestration."""

import uuid
from collections.abc import Sequence

from app.core.errors import ConflictError, NotFoundError
from app.models.item import Item
from app.repositories.item import ItemRepository
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    def __init__(self, repository: ItemRepository) -> None:
        self._repository = repository

    async def get(self, item_id: uuid.UUID) -> Item:
        item = await self._repository.get(item_id)
        if item is None:
            raise NotFoundError(f"Item {item_id} was not found.")
        return item

    async def list(self, *, limit: int, offset: int) -> tuple[Sequence[Item], int]:
        return await self._repository.list(limit=limit, offset=offset)

    async def create(self, data: ItemCreate) -> Item:
        await self._ensure_name_available(data.name)
        return await self._repository.add(Item(**data.model_dump()))

    async def update(self, item_id: uuid.UUID, data: ItemUpdate) -> Item:
        item = await self.get(item_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"] != item.name:
            await self._ensure_name_available(changes["name"])
        for field, value in changes.items():
            setattr(item, field, value)
        return await self._repository.save(item)

    async def delete(self, item_id: uuid.UUID) -> None:
        item = await self.get(item_id)
        await self._repository.delete(item)

    async def _ensure_name_available(self, name: str) -> None:
        if await self._repository.get_by_name(name) is not None:
            raise ConflictError(f"An item named {name!r} already exists.")
