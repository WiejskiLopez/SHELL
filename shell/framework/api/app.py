"""FastAPI application factory for shell control plane."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.bootstrap.config_logging.setup_logging import setup_logging
from shell.domain.exceptions import DomainError
from shell.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.framework.api.middleware.error_handler import domain_error_handler
from shell.framework.api.routers import envelopes, nodes, task_executions, workflows

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from shell.bootstrap.container.core_container import CoreContainer


def create_app(core_container: CoreContainer) -> FastAPI:
    """Create the FastAPI application with all routers and middleware."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        setup_logging()
        yield  # startup / shutdown hooks can be added here

    app = FastAPI(
        title="shell control plane",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.core_container = core_container

    # Middleware
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    # Routers
    app.include_router(task_executions.router)
    app.include_router(workflows.router)
    app.include_router(envelopes.router)
    app.include_router(nodes.router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:  # type: ignore[type-arg]
        return {"status": "ok"}

    return app
