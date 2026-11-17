"""Import every model here so ``Base.metadata`` is complete for Alembic autogenerate."""

from app.models.item import Item

__all__ = ["Item"]
