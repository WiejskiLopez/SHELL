"""FastAPI application factory for shell_ddd control plane."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from shell_ddd.bootstrap.container import Container
from shell_ddd.bootstrap.setup_logging import setup_logging
from shell_ddd.domain.exceptions import DomainError
from shell_ddd.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell_ddd.framework.api.middleware.error_handler import domain_error_handler
from shell_ddd.framework.api.routers import envelopes, nodes, tasks, workflows


def create_app(container: Container) -> FastAPI:
    """Create the FastAPI application with all routers and middleware."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        setup_logging()
        yield  # startup / shutdown hooks can be added here

    app = FastAPI(
        title="shell_ddd control plane",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.container = container

    # Middleware
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    # Routers
    app.include_router(tasks.router)
    app.include_router(workflows.router)
    app.include_router(envelopes.router)
    app.include_router(nodes.router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:  # type: ignore[type-arg]
        return {"status": "ok"}

    return app
