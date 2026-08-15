from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.ingestion.framework.ingestion.ingestion.api.router import router
from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.health import mount_readiness
from shell.platform.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell.platform.framework.api.middleware.error_handler import domain_error_handler

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


def create_ingestion_app(container: ContainerProtocol) -> FastAPI:
    app = FastAPI(title="shell - ingestion", version="0.1.0")
    app.state.core_container = container
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.include_router(router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    mount_readiness(app, container)
    return app
