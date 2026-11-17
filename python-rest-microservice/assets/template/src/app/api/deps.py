"""Dependency-injection wiring. Routes ask for what they need via the ``Annotated`` aliases
below; tests swap implementations with ``app.dependency_overrides``.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import session_scope
from app.repositories.item import SqlAlchemyItemRepository
from app.services.item import ItemService


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    # Use ``async with`` (not ``async for``) so an exception raised by the route is thrown
    # into session_scope, which rolls back and closes the session.
    async with session_scope(request.app.state.session_factory) as session:
        yield session


# scope="function": commit/rollback runs *before* the response is sent, so a failed commit
# can never be reported to the client as a success.
SessionDep = Annotated[AsyncSession, Depends(get_session, scope="function")]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_item_service(session: SessionDep) -> ItemService:
    return ItemService(SqlAlchemyItemRepository(session))


ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]


# ---------------------------------------------------------------------------
# Auth seam — provider-specific code goes ONLY here (see SKILL.md, Step 1).
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[str] = field(default_factory=frozenset)


async def get_current_principal(request: Request) -> Principal:
    """Validate the caller's credentials and return who they are.

    Implement with the auth provider the user chose (e.g. OIDC/JWKS token validation), then
    protect routes with ``principal: PrincipalDep``. Until then, the example routes are
    unauthenticated: do not deploy them beyond local/dev environments.
    """
    raise NotImplementedError("Auth provider not configured yet")


PrincipalDep = Annotated[Principal, Depends(get_current_principal)]
