"""Builds the FastAPI app. Run locally with: uvicorn app.main:app --reload"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import health, items
from app.config import Settings
from app.errors import ConflictError, NotFoundError
from app.repositories.item_repository import InMemoryItemRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title=settings.service_name)

    # Swap this for the client's real data store (see repositories/item_repository.py).
    app.state.item_repository = InMemoryItemRepository()

    # The one place where service errors become HTTP status codes.
    @app.exception_handler(NotFoundError)
    def not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    def conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    app.include_router(health.router)
    app.include_router(items.router, prefix="/api/v1")
    return app


app = create_app()
