"""The API contract for items: what clients send and what they get back."""

from uuid import UUID

from pydantic import BaseModel, Field


class ItemIn(BaseModel):
    """Request body for creating or replacing an item."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    quantity: int = Field(default=0, ge=0)


class Item(ItemIn):
    """Response body: the stored item, including its server-assigned id."""

    id: UUID
