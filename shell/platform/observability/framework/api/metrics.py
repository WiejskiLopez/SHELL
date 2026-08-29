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

if TYPE_CHECKING:
    from fastapi import FastAPI

    from shell.platform.framework.api.dependencies import ContainerProtocol

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


def mount_metrics(app: FastAPI, core_container: ContainerProtocol | Any) -> None:
    """Mount ``GET /metrics`` when the container exposes a metrics exporter."""
    exporter = getattr(core_container, "metrics_exporter", None)
    if exporter is None:
        return
    inbox = getattr(core_container, "inbox_metrics_service", None)
    outbox = getattr(core_container, "outbox_metrics_service", None)
    app.include_router(
        create_metrics_router(exporter(), inbox_provider=inbox, outbox_provider=outbox)
    )


def install_metrics(
    app: FastAPI,
    core_container: ContainerProtocol | Any,
    *,
    service: str,
) -> None:
    """Mount the metrics middleware (outermost) and the ``/metrics`` router."""
    exporter = getattr(core_container, "metrics_exporter", None)
    if exporter is None:
        return
    app.add_middleware(MetricsMiddleware, recorder=exporter(), service=service)
    mount_metrics(app, core_container)
