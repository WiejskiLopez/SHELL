"""FastAPI application factory — BC User."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from shell.framework.user.user.api.router import router as users_router
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler


def create_user_app(core_container: Any) -> FastAPI:
    """Tworzy aplikację FastAPI dla BC User."""
    app = FastAPI(title="shell — user", version="0.1.0")
    app.state.core_container = core_container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(users_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app
