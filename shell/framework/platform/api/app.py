"""FastAPI application factory for shell control plane."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.bootstrap.platform.config_logging.setup_logging import setup_logging
from shell.domain.platform.exceptions import DomainError
from shell.framework.definition.api.routers import definitions as definitions_router
from shell.framework.execution.api.routers import (
    graph_node_execution,
    task_executions,
    workflows,
)
from shell.framework.platform.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.framework.platform.api.middleware.error_handler import domain_error_handler
from shell.framework.projekt.api.routers import projects as projects_router
from shell.framework.session.api.routers import sessions as sessions_router
from shell.framework.user.api.routers import users as users_router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from shell.bootstrap.platform.container.core_container import CoreContainer


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
    app.include_router(graph_node_execution.router)
    app.include_router(definitions_router.router, prefix="/api/v1")
    app.include_router(sessions_router.router, prefix="/api/v1")
    app.include_router(users_router.router, prefix="/api/v1")
    app.include_router(projects_router.router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app
