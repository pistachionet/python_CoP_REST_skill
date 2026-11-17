"""API contract for the ``Item`` resource. Separate models per use: create, update, read."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import Field, model_validator

from app.schemas.common import ApiModel


class ItemBase(ApiModel):
    name: str = Field(min_length=1, max_length=100, examples=["Widget"])
    description: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2, examples=["9.99"])


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ApiModel):
    """PATCH body — every field optional; only fields that are sent get updated."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)

    @model_validator(mode="after")
    def _reject_null_for_required_fields(self) -> Self:
        # "Omitted" means "leave unchanged"; an explicit null on a required column is an error.
        for field in ("name", "price"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' cannot be null")
        return self


class ItemRead(ItemBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
