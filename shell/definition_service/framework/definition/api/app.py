"""FastAPI application factory — BC Definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.definition_service.framework.definition.graph_definition.api.router import (
    router as graph_definitions_router,
)
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.api_key import AuthMiddleware
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler
from shell.platform.framework.api.openapi import configure_openapi
from shell.platform.observability.framework.api.health import mount_readiness
from shell.platform.observability.framework.api.metrics import install_metrics

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


DEFINITION_OPENAPI_TAGS = (
    {"name": "GraphDefinitions", "description": "Graph definition operations."},
    {"name": "Health", "description": "Service health and readiness."},
)


def create_definition_app(core_container: ContainerProtocol, *, api_key: str = "") -> FastAPI:
    """Tworzy aplikację FastAPI dla BC Definition."""
    app = FastAPI(title="shell — definition", version="0.1.0")
    app.state.core_container = core_container

    app.add_middleware(CorrelationIdMiddleware)
    if api_key:
        app.add_middleware(
            AuthMiddleware,
            api_key=api_key,
            public_exact={"/health", "/readiness", "/metrics"},
            public_prefix={"/docs", "/redoc", "/openapi.json"},
        )
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(graph_definitions_router, prefix="/api/v1")
    configure_openapi(app, tags=DEFINITION_OPENAPI_TAGS)

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    mount_readiness(app, core_container)
    install_metrics(app, core_container, service="definition")
    return app
