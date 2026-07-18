"""FastAPI application factory — BC Session."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.framework.session.session.api.router import router as sessions_router
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.core_container import CoreContainer


def create_session_app(core_container: CoreContainer) -> FastAPI:
    """Tworzy aplikację FastAPI dla BC Session."""
    app = FastAPI(title="shell — session", version="0.1.0")
    app.state.core_container = core_container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(sessions_router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app
