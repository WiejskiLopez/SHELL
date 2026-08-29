"""Metrics router — exposes the service Prometheus ``/metrics`` endpoint.

Before rendering, the endpoint refreshes the inbox and outbox backlog snapshots
from the container providers so the exported gauges reflect current state on
every scrape. Failures here must never break the scrape itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Response

from shell.platform.observability.application.ports.metrics import MetricsExporter
from shell.platform.observability.framework.api.middleware.metrics import MetricsMiddleware
from shell.platform.observability.framework.api.providers import ObservabilityProviders

if TYPE_CHECKING:
    from fastapi import FastAPI

PROMETHEUS_MEDIA_TYPE = "text/plain; version=0.0.4; charset=utf-8"


async def _refresh(provider: Any) -> None:
    if provider is None:
        return
    try:
        await provider().snapshot()
    except Exception:
        return


def create_metrics_router(
    exporter: MetricsExporter,
    *,
    inbox_provider: Any = None,
    outbox_provider: Any = None,
) -> APIRouter:
    router = APIRouter(tags=["Metrics"])

    @router.get("/metrics")
    async def metrics() -> Response:
        await _refresh(inbox_provider)
        await _refresh(outbox_provider)
        return Response(
            content=exporter.render(),
            media_type=PROMETHEUS_MEDIA_TYPE,
        )

    return router


def mount_metrics(app: FastAPI, providers: ObservabilityProviders) -> None:
    """Mount ``GET /metrics``.

    Błąd providu jest twardy (AttributeError przy braku ``metrics_exporter``),
    a nie cichym brakiem endpointu — kontener, który deklaruje obserwowalność,
    musi ją realnie wystawić.
    """
    exporter = providers.metrics_exporter()
    app.include_router(
        create_metrics_router(
            exporter,
            inbox_provider=providers.inbox_metrics_service,
            outbox_provider=providers.outbox_metrics_service,
        )
    )


def install_metrics(
    app: FastAPI,
    providers: ObservabilityProviders,
    *,
    service: str,
) -> None:
    """Mount the metrics middleware (outermost) and the ``/metrics`` router."""
    exporter = providers.metrics_exporter()
    app.add_middleware(MetricsMiddleware, recorder=exporter, service=service)
    mount_metrics(app, providers)
