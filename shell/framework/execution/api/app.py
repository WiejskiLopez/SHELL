"""FastAPI application factory — BC Execution."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from shell.framework.execution.edge_execution.api.router import router as edge_executions_router
from shell.framework.execution.edge_link_execution.api.router import (
    router as edge_link_executions_router,
)
from shell.framework.execution.node_execution.api.router import router as node_execution_router
from shell.framework.execution.workflow.api.router import router as workflows_router
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler


def create_execution_app(core_container: Any) -> FastAPI:
    """Tworzy aplikację FastAPI dla BC Execution."""
    app = FastAPI(title="shell — execution", version="0.1.0")
    app.state.core_container = core_container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(edge_executions_router)
    app.include_router(edge_link_executions_router)
    app.include_router(workflows_router)
    app.include_router(node_execution_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app
