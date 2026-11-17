"""Aggregate routers. Business routes are versioned under /api/v1; health is unversioned."""

from fastapi import APIRouter

from app.api import health
from app.api.v1 import items

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(items.router)

root = APIRouter()
root.include_router(health.router)
root.include_router(api_v1)
