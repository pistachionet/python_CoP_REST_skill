"""HTTP routes for ``Item``. Thin: validate input, call the service, shape the response."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, status

from app.api.deps import ItemServiceDep
from app.schemas.common import Page, PageParams
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

PROBLEM_RESPONSES: dict[int | str, dict[str, str]] = {
    404: {"description": "Item not found (problem+json)"},
    409: {"description": "Name already in use (problem+json)"},
}


@router.get("", response_model=Page[ItemRead])
async def list_items(
    service: ItemServiceDep, page: Annotated[PageParams, Query()]
) -> Page[ItemRead]:
    items, total = await service.list(limit=page.limit, offset=page.offset)
    return Page[ItemRead](
        items=[ItemRead.model_validate(i) for i in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.post(
    "",
    response_model=ItemRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: PROBLEM_RESPONSES[409]},
)
async def create_item(
    data: ItemCreate, service: ItemServiceDep, request: Request, response: Response
) -> ItemRead:
    item = ItemRead.model_validate(await service.create(data))
    response.headers["Location"] = str(request.url_for("get_item", item_id=item.id))
    return item


@router.get("/{item_id}", response_model=ItemRead, responses={404: PROBLEM_RESPONSES[404]})
async def get_item(item_id: uuid.UUID, service: ItemServiceDep) -> ItemRead:
    return ItemRead.model_validate(await service.get(item_id))


@router.patch("/{item_id}", response_model=ItemRead, responses=PROBLEM_RESPONSES)
async def update_item(item_id: uuid.UUID, data: ItemUpdate, service: ItemServiceDep) -> ItemRead:
    return ItemRead.model_validate(await service.update(item_id, data))


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: PROBLEM_RESPONSES[404]},
)
async def delete_item(item_id: uuid.UUID, service: ItemServiceDep) -> None:
    await service.delete(item_id)
