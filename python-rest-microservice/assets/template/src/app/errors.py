"""Errors the service raises on purpose. Plain Python: no web-framework imports here.

``main.py`` maps each one to an HTTP status code in a single place.
"""


class NotFoundError(Exception):
    """The requested resource does not exist (HTTP 404)."""


class ConflictError(Exception):
    """The request conflicts with existing data, e.g. a duplicate name (HTTP 409)."""
