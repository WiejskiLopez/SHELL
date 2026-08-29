"""Unit tests — ResilientAsyncClient records outbound/retry/circuit metrics."""

from __future__ import annotations

import httpx
import pytest

from shell.platform.infrastructure.context.client import ResilientAsyncClient
from shell.platform.infrastructure.context.resilience import (
    CircuitBreakerPolicy,
    CircuitOpenError,
    RetryPolicy,
)
from shell.platform.observability.infrastructure.metrics.registry import MetricsRegistry


class _DownstreamApp:
    def __init__(self, status: int = 503) -> None:
        self.status = status
        self.requests = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests += 1
        return httpx.Response(self.status, request=request, json={"detail": "unavailable"})


class TestResilientAsyncClientMetrics:
    async def test_records_attempts_and_retries_on_503(self) -> None:
        downstream = _DownstreamApp(status=503)
        registry = MetricsRegistry()
        async with ResilientAsyncClient(
            transport=httpx.MockTransport(downstream.handler),
            base_url="http://definition",
            service_api_key="key",
            retry_policy=RetryPolicy(max_attempts=3, initial_delay=0.0, max_delay=0.0, jitter=0.0),
            metrics=registry,
            metrics_target="definition",
        ) as client:
            response = await client.get("/api/v1/graph-definitions/1")

        assert response.status_code == 503
        assert downstream.requests == 3
        output = registry.render()
        assert (
            'http_outbound_requests_total{target_service="definition",method="GET"} 3.0' in output
        )
        assert 'http_outbound_retries_total{target_service="definition",method="GET"} 2.0' in output

    async def test_records_circuit_trip_and_rejects(self) -> None:
        downstream = _DownstreamApp(status=503)
        registry = MetricsRegistry()
        async with ResilientAsyncClient(
            transport=httpx.MockTransport(downstream.handler),
            base_url="http://definition",
            retry_policy=RetryPolicy(max_attempts=1),
            circuit_breaker_policy=CircuitBreakerPolicy(failure_threshold=1),
            metrics=registry,
            metrics_target="definition",
        ) as client:
            await client.get("/api/v1/graph-definitions/1")
            with pytest.raises(CircuitOpenError):
                await client.get("/api/v1/graph-definitions/1")

        output = registry.render()
        assert (
            'http_outbound_circuit_trips_total{target_service="definition",method="GET"} 1.0'
            in output
        )
        assert (
            'http_outbound_circuit_rejects_total{target_service="definition",method="GET"} 1.0'
            in output
        )

    async def test_success_records_circuit_state_closed(self) -> None:
        downstream = _DownstreamApp(status=200)
        registry = MetricsRegistry()
        async with ResilientAsyncClient(
            transport=httpx.MockTransport(downstream.handler),
            base_url="http://definition",
            metrics=registry,
            metrics_target="definition",
        ) as client:
            response = await client.get("/api/v1/graph-definitions/1")

        assert response.status_code == 200
        output = registry.render()
        assert (
            'http_outbound_requests_total{target_service="definition",method="GET"} 1.0' in output
        )
        assert 'http_outbound_circuit_state{target_service="definition",method="GET"} 0.0' in output
