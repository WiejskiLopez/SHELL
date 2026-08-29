"""E2E — /metrics exposes Prometheus text metrics for a real service app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import _make_app

if TYPE_CHECKING:
    import pathlib


class TestMetricsEndpoint:
    async def test_metrics_endpoint_returns_prometheus_text(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.get("/health")
            response = await client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        body = response.text
        assert "# TYPE http_requests_total counter" in body
        assert 'http_requests_total{service="execution",method="GET",status="200"}' in body
        assert "# TYPE http_request_duration_seconds histogram" in body

    async def test_metrics_include_backlog_gauges(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/metrics")

        assert response.status_code == 200
        body = response.text
        assert "# TYPE inbox_backlog_pending gauge" in body
        assert "# TYPE outbox_backlog_pending gauge" in body
