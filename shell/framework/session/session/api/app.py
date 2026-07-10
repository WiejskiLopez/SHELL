"""FastAPI application factory — Session aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.framework.session.session.api.router import router
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.core_container import CoreContainer


def create_session_app(container: CoreContainer) -> FastAPI:
    """Tworzy aplikację FastAPI dla agregatu Session.

    Może być używana jako samodzielny mikroserwis lub jako część BC Session.
    """
    app = FastAPI(title="shell — session:session", version="0.1.0")
    app.state.core_container = container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app
