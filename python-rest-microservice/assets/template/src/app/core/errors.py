"""Domain exceptions.

Services raise these. They are plain Python exceptions with no web-framework imports, so the
service layer stays independent of FastAPI. ``app/api/errors.py`` is the single place where
they are translated into HTTP responses.
"""

from http import HTTPStatus


class DomainError(Exception):
    """Base class for errors the service raises on purpose."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    title: str = "Internal Server Error"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    status_code = HTTPStatus.NOT_FOUND
    title = "Resource Not Found"


class ConflictError(DomainError):
    status_code = HTTPStatus.CONFLICT
    title = "Conflict"


class BusinessRuleError(DomainError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    title = "Business Rule Violation"
