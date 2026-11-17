"""Liveness and readiness probes — the contract any container platform can use.

* ``/health/live``  — the process is up. No dependency checks (a DB outage must not cause
  restarts).
* ``/health/ready`` — the service can do useful work. Checks critical dependencies.
"""

import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", responses={503: {"description": "A dependency is unavailable"}})
async def ready(request: Request) -> JSONResponse:
    try:
        async with request.app.state.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.warning("Readiness check failed: database unreachable", exc_info=True)
        return JSONResponse(
            {"status": "unavailable", "checks": {"database": "down"}},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return JSONResponse({"status": "ok", "checks": {"database": "up"}})
