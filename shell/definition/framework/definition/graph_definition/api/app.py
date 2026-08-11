"""FastAPI application factory — GraphDefinition aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.definition.framework.definition.graph_definition.api.router import router
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


def create_graph_definition_app(container: ContainerProtocol) -> FastAPI:
    """Tworzy aplikację FastAPI dla agregatu GraphDefinition.

    Może być używana jako samodzielny mikroserwis lub jako część BC Definition.
    """
    app = FastAPI(title="shell — definition:graph_definition", version="0.1.0")
    app.state.core_container = container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(router)

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app
