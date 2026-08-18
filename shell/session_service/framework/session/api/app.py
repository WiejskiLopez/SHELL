"""FastAPI application factory — BC Session."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from shell.platform.domain.exceptions import DomainError
from shell.platform.framework.api.middleware.correlation_id import (
    CorrelationIdMiddleware,
)
from shell.platform.framework.api.middleware.error_handler import domain_error_handler
from shell.platform.framework.api.openapi import configure_openapi
from shell.platform.framework.api.readiness import create_readiness_router
from shell.session_service.framework.session.session.api.router import router as sessions_router

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


SESSION_OPENAPI_TAGS = (
    {"name": "Sessions", "description": "Session lifecycle operations."},
    {"name": "Health", "description": "Service health and readiness."},
)


def create_session_app(core_container: ContainerProtocol) -> FastAPI:
    """Tworzy aplikację FastAPI dla BC Session."""
    app = FastAPI(title="shell — session", version="0.1.0")
    app.state.core_container = core_container

    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    app.include_router(sessions_router, prefix="/api/v1")
    configure_openapi(app, tags=SESSION_OPENAPI_TAGS)

    readiness_probe = getattr(core_container, "readiness_probe", None)
    if readiness_probe is not None:
        app.include_router(create_readiness_router(readiness_probe()))

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, object]:
        payload: dict[str, object] = {"status": "ok"}
        metrics_provider = getattr(core_container, "inbox_metrics_service", None)
        if metrics_provider is not None:
            try:
                metrics_service = metrics_provider()
                metrics = await metrics_service.snapshot()
                payload["backlog"] = {
                    "pending": metrics.pending,
                    "processing": metrics.processing,
                    "retry": metrics.retry,
                    "dead_letter": metrics.dead_letter,
                    "total": metrics.total,
                    "oldest_pending_age_seconds": metrics.oldest_pending_age_seconds,
                }
            except Exception:
                payload["backlog"] = {"status": "unavailable"}
        return payload

    return app
