"""Wiring: decides which implementations each request gets.

Routes ask for ``ItemServiceDep``; tests can swap it via ``app.dependency_overrides``.
"""

from typing import Annotated

from fastapi import Depends, Request

from app.services.item_service import ItemService


def get_item_service(request: Request) -> ItemService:
    return ItemService(request.app.state.item_repository)


ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]
