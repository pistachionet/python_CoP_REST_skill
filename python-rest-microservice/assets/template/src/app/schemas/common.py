"""Shared API contract types."""

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    """Base for all request/response schemas: reject unknown fields, read from ORM objects."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class PageParams(ApiModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class Page[T](ApiModel):
    """Offset-paginated collection envelope."""

    items: list[T]
    total: int
    limit: int
    offset: int
