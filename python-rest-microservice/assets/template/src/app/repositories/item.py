"""Data access for ``Item``. The only layer that issues SQL.

``ItemRepository`` is the interface (a Protocol) the service depends on. The SQLAlchemy class
is the production implementation; unit tests substitute an in-memory fake.
"""

import uuid
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item


class ItemRepository(Protocol):
    async def get(self, item_id: uuid.UUID) -> Item | None: ...
    async def get_by_name(self, name: str) -> Item | None: ...
    async def list(self, *, limit: int, offset: int) -> tuple[Sequence[Item], int]: ...
    async def add(self, item: Item) -> Item: ...
    async def save(self, item: Item) -> Item: ...
    async def delete(self, item: Item) -> None: ...


class SqlAlchemyItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, item_id: uuid.UUID) -> Item | None:
        return await self._session.get(Item, item_id)

    async def get_by_name(self, name: str) -> Item | None:
        result = await self._session.execute(select(Item).where(Item.name == name))
        return result.scalar_one_or_none()

    async def list(self, *, limit: int, offset: int) -> tuple[Sequence[Item], int]:
        total = await self._session.scalar(select(func.count()).select_from(Item))
        result = await self._session.execute(
            select(Item).order_by(Item.created_at, Item.id).limit(limit).offset(offset)
        )
        return result.scalars().all(), total or 0

    async def add(self, item: Item) -> Item:
        self._session.add(item)
        return await self.save(item)

    async def save(self, item: Item) -> Item:
        # Flush to surface DB errors now; refresh to load server-generated columns
        # (timestamps) without triggering lazy I/O later.
        await self._session.flush()
        await self._session.refresh(item)
        return item

    async def delete(self, item: Item) -> None:
        await self._session.delete(item)
        await self._session.flush()
