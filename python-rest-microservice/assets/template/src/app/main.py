"""Application factory and ASGI entry point (``uvicorn app.main:app``)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __doc__ as service_doc
from app.api.errors import register_exception_handlers
from app.api.router import root
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import create_engine, create_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a fully configured app. Tests pass their own ``Settings``."""
    settings = settings or get_settings()
    configure_logging(
        settings.log_level, json_output=settings.log_json, service_name=settings.service_name
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Process-wide resources: created once at startup, disposed at shutdown.
        engine = create_engine(settings)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        yield
        await engine.dispose()

    docs = settings.docs_enabled and settings.environment != "prod"
    app = FastAPI(
        title=settings.service_name,
        description=service_doc or "",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.settings = settings
    register_exception_handlers(app)
    app.include_router(root)
    return app


app = create_app()
