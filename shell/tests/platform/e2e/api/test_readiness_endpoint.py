"""E2E — /readiness reflects the composite probe and answers 503 with diagnostics."""

from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from shell.platform.observability.application.ports.readiness import ReadinessProbe, ReadinessReport
from shell.platform.observability.framework.api.readiness import create_readiness_router
from shell.platform.observability.infrastructure.health.composite_readiness_probe import (
    CompositeReadinessProbe,
)


class _StubProbe(ReadinessProbe):
    def __init__(self, ready: bool, checks: dict[str, object]) -> None:
        self._ready = ready
        self._checks = checks

    async def check(self) -> ReadinessReport:
        return ReadinessReport(ready=self._ready, checks=self._checks)


def _ready(name: str) -> _StubProbe:
    return _StubProbe(True, {name: True})


def _failed(name: str) -> _StubProbe:
    return _StubProbe(False, {name: "error: down"})


def _app(probe: ReadinessProbe) -> FastAPI:
    app = FastAPI()
    app.include_router(create_readiness_router(probe))
    return app


class TestReadinessEndpoint:
    async def test_ready_returns_200_when_all_checks_pass(self) -> None:
        app = _app(CompositeReadinessProbe([_ready("database"), _ready("broker")]))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/readiness")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["checks"] == {"database": True, "broker": True}

    async def test_broker_down_returns_503_with_diagnostic(self) -> None:
        app = _app(CompositeReadinessProbe([_ready("database"), _failed("broker")]))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/readiness")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "not_ready"
        assert body["checks"]["database"] is True
        assert body["checks"]["broker"] == "error: down"
