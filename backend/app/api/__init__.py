"""HTTP API routers for FinAlly.

Each concern owns one module under ``app/api/`` (e.g. ``health.py``) and exposes
a ``router`` symbol. ``build_api_router()`` aggregates them and returns a single
``APIRouter`` that ``app/main.py`` mounts at ``/api``.
"""

from __future__ import annotations

from fastapi import APIRouter

from . import health


def build_api_router() -> APIRouter:
    """Build the aggregated API router.

    Side-effect free: returns a fresh ``APIRouter`` each call. Tests can mount
    it on isolated apps without touching module-level state.
    """
    router = APIRouter()
    router.include_router(health.router)
    return router


api_router: APIRouter = build_api_router()

__all__ = ["api_router", "build_api_router"]
