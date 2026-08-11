"""FastAPI application factory — Project aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler
from shell.project.framework.project.project.api.router import router

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


def create_project_app(container: ContainerProtocol) -> FastAPI:
    """Tworzy aplikację FastAPI dla agregatu Project.

    Może być używana jako samodzielny mikroserwis lub jako część BC Project.
    """
    app = FastAPI(title="shell — project:project", version="0.1.0")
    app.state.core_container = container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app
