"""FastAPI application factory for shell control plane."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from shell.framework.definition.graph_definition.api.router import (
    router as graph_definitions_router,
)
from shell.framework.execution.edge_execution.api.router import router as edge_executions_router
from shell.framework.execution.edge_link_execution.api.router import (
    router as edge_link_executions_router,
)
from shell.framework.execution.node_execution.api.router import router as node_execution_router
from shell.framework.execution.task_execution.api.router import router as task_executions_router
from shell.framework.execution.workflow.api.router import router as workflows_router
from shell.framework.messaging.message_router.api.router import router as message_routers_router
from shell.framework.project.project.api.router import router as projects_router
from shell.framework.scheduling.scheduler_definition.api.router import (
    router as scheduler_definitions_router,
)
from shell.framework.scheduling.scheduler_execution.api.router import (
    router as scheduler_executions_router,
)
from shell.framework.scheduling.scheduler_job.api.router import router as scheduler_jobs_router
from shell.framework.session.session.api.router import router as sessions_router
from shell.framework.user.auth_session.api.router import router as auth_sessions_router
from shell.framework.user.user.api.router import router as users_router
from shell.platform.application.exceptions import ApplicationError
from shell.platform.bootstrap.config_logging.setup_logging import setup_logging
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.api_key import AuthMiddleware
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import (
    application_error_handler,
    domain_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from shell.platform.framework.api.openapi import configure_openapi
from shell.platform.framework.api.setup import resolve_api_key, resolve_jwt_secret

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
    configure_openapi(app)

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8080",
            "http://localhost:3010",
            "http://localhost:3011",
            "http://localhost:3012",
            "http://localhost:3013",
            "http://localhost:3014",
            "http://localhost:3015",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Correlation-ID"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        AuthMiddleware,
        api_key=resolve_api_key(core_container),
        jwt_secret=resolve_jwt_secret(core_container),
    )
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ApplicationError, application_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Routers — wszystkie agregaty pod /api/v1/ dla spójnego versionowania
    app.include_router(edge_executions_router, prefix="/api/v1")
    app.include_router(edge_link_executions_router, prefix="/api/v1")
    app.include_router(workflows_router, prefix="/api/v1")
    app.include_router(task_executions_router, prefix="/api/v1")
    app.include_router(node_execution_router, prefix="/api/v1")
    app.include_router(graph_definitions_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(auth_sessions_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(message_routers_router, prefix="/api/v1")
    app.include_router(scheduler_definitions_router, prefix="/api/v1")
    app.include_router(scheduler_jobs_router, prefix="/api/v1")
    app.include_router(scheduler_executions_router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


# Alias — backward compat dla istniejącego entrypoint
create_app = create_monolith_app
