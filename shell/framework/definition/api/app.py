"""FastAPI application factory — BC Definition."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from shell.framework.definition.graph_definition.api.router import router as graph_definitions_router
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler


def create_definition_app(core_container: Any) -> FastAPI:
    """Tworzy aplikację FastAPI dla BC Definition."""
    app = FastAPI(title="shell — definition", version="0.1.0")
    app.state.core_container = core_container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(graph_definitions_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app
