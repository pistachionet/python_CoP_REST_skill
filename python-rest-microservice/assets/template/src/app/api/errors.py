"""Translate exceptions into RFC 9457 ``application/problem+json`` responses.

This is the only module that maps errors to HTTP. Handlers are registered once in the app
factory, so individual routes never build error responses by hand.
"""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import DomainError

logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"


def problem_response(
    request: Request,
    status_code: int,
    title: str,
    detail: str | None = None,
    **extra: Any,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "instance": request.url.path,
    }
    if detail is not None:
        body["detail"] = detail
    body.update(extra)
    return JSONResponse(body, status_code=status_code, media_type=PROBLEM_JSON)


async def _domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)  # noqa: S101 - narrows the type for mypy
    return problem_response(request, exc.status_code, exc.title, exc.detail)


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)  # noqa: S101
    errors = [
        {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]} for err in exc.errors()
    ]
    return problem_response(
        request,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "Request Validation Failed",
        "One or more fields are invalid.",
        errors=errors,
    )


async def _http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Covers framework-raised errors such as 404 for unknown routes and 405.
    assert isinstance(exc, StarletteHTTPException)  # noqa: S101
    title = HTTPStatus(exc.status_code).phrase
    detail = exc.detail if isinstance(exc.detail, str) and exc.detail != title else None
    return problem_response(request, exc.status_code, title, detail)


async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the stack trace server-side; never leak internals to the client.
    logger.exception("Unhandled error", exc_info=exc)
    return problem_response(request, HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
