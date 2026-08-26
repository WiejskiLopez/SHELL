"""FastAPI application factory — BC Execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.execution_service.framework.execution.edge_execution.api.router import (
    router as edge_executions_router,
)
from shell.execution_service.framework.execution.edge_link_execution.api.router import (
    router as edge_link_executions_router,
)
from shell.execution_service.framework.execution.node_execution.api.router import (
    router as node_execution_router,
)
from shell.execution_service.framework.execution.task_execution.api.router import (
    router as task_executions_router,
)
from shell.execution_service.framework.execution.workflow.api.router import (
    router as workflows_router,
)
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.health import mount_readiness
from shell.platform.framework.api.middleware.api_key import AuthMiddleware
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler
from shell.platform.framework.api.openapi import configure_openapi

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


EXECUTION_OPENAPI_TAGS = (
    {"name": "Workflows", "description": "Workflow execution operations."},
    {"name": "Task Executions", "description": "Task execution operations."},
    {"name": "NodeExecutions", "description": "Node execution result operations."},
    {"name": "EdgeExecutions", "description": "Workflow edge execution operations."},
    {"name": "EdgeLinkExecutions", "description": "Workflow edge link operations."},
    {"name": "Health", "description": "Service health and readiness."},
)


def create_execution_app(
    core_container: ContainerProtocol,
    *,
    include_routes: bool = True,
    api_key: str = "",
) -> FastAPI:
    """Tworzy aplikację FastAPI dla BC Execution."""
    app = FastAPI(title="shell — execution", version="0.1.0")
    app.state.core_container = core_container

    app.add_middleware(CorrelationIdMiddleware)
    if api_key:
        app.add_middleware(
            AuthMiddleware,
            api_key=api_key,
            public_exact={"/health", "/readiness"},
            public_prefix={"/docs", "/redoc", "/openapi.json"},
        )
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    if include_routes:
        app.include_router(edge_executions_router, prefix="/api/v1")
        app.include_router(edge_link_executions_router, prefix="/api/v1")
        app.include_router(workflows_router, prefix="/api/v1")
        app.include_router(task_executions_router, prefix="/api/v1")
        app.include_router(node_execution_router, prefix="/api/v1")

    configure_openapi(
        app,
        tags=EXECUTION_OPENAPI_TAGS if include_routes else EXECUTION_OPENAPI_TAGS[-1:],
    )

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    mount_readiness(app, core_container)
    return app
