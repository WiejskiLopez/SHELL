"""Readiness router — exposes a probe-backed GET /readiness endpoint.

``/health`` remains the liveness signal; ``/readiness`` reflects real readiness
(DB, migrations, worker activity, backlog) and answers 503 with a diagnostic
body until the process can do useful work.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Response

if TYPE_CHECKING:
    from shell.platform.application.ports.readiness import ReadinessProbe


def create_readiness_router(probe: ReadinessProbe) -> APIRouter:
    router = APIRouter(tags=["Health"])

    @router.get("/readiness")
    async def readiness(response: Response) -> dict[str, object]:
        report = await probe.check()
        payload: dict[str, object] = {
            "status": "ready" if report.ready else "not_ready",
            "checks": report.checks,
        }
        if not report.ready:
            response.status_code = 503
        return payload

    return router
