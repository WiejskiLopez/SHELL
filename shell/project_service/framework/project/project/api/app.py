"""FastAPI application factory — Project aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.api_key import AuthMiddleware
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler
from shell.platform.framework.api.openapi import configure_openapi
from shell.platform.observability.framework.api.health import mount_readiness
from shell.platform.observability.framework.api.metrics import install_metrics
from shell.project_service.framework.project.project.api.router import router

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


PROJECT_OPENAPI_TAGS = (
    {"name": "Projects", "description": "Project management operations."},
    {"name": "Health", "description": "Service health and readiness."},
)


def create_project_app(container: ContainerProtocol, *, api_key: str = "") -> FastAPI:
    """Tworzy aplikację FastAPI dla agregatu Project.

    Może być używana jako samodzielny mikroserwis lub jako część BC Project.
    """
    app = FastAPI(title="shell — project:project", version="0.1.0")
    app.state.core_container = container

    app.add_middleware(CorrelationIdMiddleware)
    if api_key:
        app.add_middleware(
            AuthMiddleware,
            api_key=api_key,
            public_exact={"/health", "/readiness", "/metrics"},
            public_prefix={"/docs", "/redoc", "/openapi.json"},
        )
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(router, prefix="/api/v1")
    configure_openapi(app, tags=PROJECT_OPENAPI_TAGS)

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    mount_readiness(app, container)
    install_metrics(app, container, service="project")
    return app
