"""FastAPI application factory for shell control plane."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from shell.framework.definition.graph_definition.api.router import (
    router as graph_definitions_router,
)
from shell.framework.execution.edge_execution.api.router import router as edge_executions_router
from shell.framework.execution.edge_link_execution.api.router import (
    router as edge_link_executions_router,
)
from shell.framework.execution.node_execution.api.router import router as node_execution_router
from shell.framework.execution.workflow.api.router import router as workflows_router
from shell.framework.project.project.api.router import router as projects_router
from shell.framework.session.session.api.router import router as sessions_router
from shell.framework.user.user.api.router import router as users_router
from shell.platform.bootstrap.config_logging.setup_logging import setup_logging
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import (
    domain_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_error_handler,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from shell.platform.bootstrap.container.core_container import CoreContainer


def create_monolith_app(core_container: CoreContainer) -> FastAPI:
    """Tworzy monolityczną aplikację FastAPI ze wszystkimi BC.

    Przy ekstrakcji mikroserwisu (BC) użyj dedykowanej fabryki:
      - framework/execution/api/app.py  → create_execution_app()
      - framework/definition/api/app.py → create_definition_app()
      - framework/user/api/app.py       → create_user_app()
      - framework/session/api/app.py    → create_session_app()

    Przy ekstrakcji pojedynczego agregatu użyj fabryki per-aggregate:
      - framework/execution/workflow/api/app.py           → create_workflow_app()
      - framework/execution/node_execution/api/app.py     → create_node_execution_app()
      - framework/execution/edge_execution/api/app.py     → create_edge_execution_app()
      - framework/execution/edge_link_execution/api/app.py → create_edge_link_execution_app()
      - framework/definition/graph_definition/api/app.py  → create_graph_definition_app()
      - framework/session/session/api/app.py              → create_session_app()
      - framework/user/user/api/app.py                    → create_user_app()
      - framework/project/project/api/app.py              → create_project_app()
    """

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
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Routers
    app.include_router(edge_executions_router)
    app.include_router(edge_link_executions_router)
    app.include_router(workflows_router)
    app.include_router(node_execution_router)
    app.include_router(graph_definitions_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


# Alias — backward compat dla istniejącego entrypoint
create_app = create_monolith_app
