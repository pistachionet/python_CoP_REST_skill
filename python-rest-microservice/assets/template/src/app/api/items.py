"""HTTP routes for items. Keep these thin: take the request, call the service, return."""

from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies import ItemServiceDep
from app.schemas.item import Item, ItemIn

router = APIRouter(prefix="/items", tags=["items"])


@router.get("")
def list_items(service: ItemServiceDep) -> list[Item]:
    return service.list_items()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_item(data: ItemIn, service: ItemServiceDep) -> Item:
    return service.create_item(data)


@router.get("/{item_id}")
def get_item(item_id: UUID, service: ItemServiceDep) -> Item:
    return service.get_item(item_id)


@router.put("/{item_id}")
def replace_item(item_id: UUID, data: ItemIn, service: ItemServiceDep) -> Item:
    return service.replace_item(item_id, data)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: UUID, service: ItemServiceDep) -> None:
    service.delete_item(item_id)
