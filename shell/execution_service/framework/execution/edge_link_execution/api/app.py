"""FastAPI application factory — EdgeLinkExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.execution_service.framework.execution.edge_link_execution.api.router import router
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


def create_edge_link_execution_app(container: ContainerProtocol) -> FastAPI:
    """Tworzy aplikację FastAPI dla agregatu EdgeLinkExecution.

    Może być używana jako samodzielny mikroserwis lub jako część BC Execution.
    """
    app = FastAPI(title="shell — execution:edge_link_execution", version="0.1.0")
    app.state.core_container = container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(router)

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
