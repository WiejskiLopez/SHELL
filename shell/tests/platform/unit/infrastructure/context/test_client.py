from __future__ import annotations

import httpx
import pytest

from shell.platform.infrastructure.context.client import (
    CorrelationIdAsyncClient,
    ResilientAsyncClient,
)
from shell.platform.infrastructure.context.resilience import (
    CircuitBreakerPolicy,
    CircuitOpenError,
    RetryPolicy,
)


@pytest.mark.asyncio
async def test_client_adds_service_api_key_to_outgoing_request() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        return httpx.Response(204)

    async with CorrelationIdAsyncClient(
        service_api_key="service-secret",
        transport=httpx.MockTransport(handler),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 204
    assert seen_headers["x-api-key"] == "service-secret"


@pytest.mark.asyncio
async def test_client_does_not_override_explicit_service_api_key() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        return httpx.Response(204)

    async with CorrelationIdAsyncClient(
        service_api_key="default-secret",
        transport=httpx.MockTransport(handler),
        base_url="http://test",
    ) as client:
        await client.get("/health", headers={"X-API-Key": "request-secret"})

    assert seen_headers["x-api-key"] == "request-secret"


@pytest.mark.asyncio
async def test_resilient_client_retries_get_after_transient_failure() -> None:
    statuses = iter((503, 204))
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(next(statuses))

    async def sleeper(delay: float) -> None:
        delays.append(delay)

    async with ResilientAsyncClient(
        retry_policy=RetryPolicy(max_attempts=2, initial_delay=0.25, max_delay=1),
        transport=httpx.MockTransport(handler),
        sleeper=sleeper,
        base_url="http://test",
    ) as client:
        response = await client.get("/resource")

    assert response.status_code == 204
    assert attempts == 2
    assert delays == [0.25]


@pytest.mark.asyncio
async def test_resilient_client_does_not_retry_post() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    async with ResilientAsyncClient(
        retry_policy=RetryPolicy(max_attempts=3),
        transport=httpx.MockTransport(handler),
        base_url="http://test",
    ) as client:
        response = await client.post("/resource")

    assert response.status_code == 503
    assert attempts == 1


@pytest.mark.asyncio
async def test_resilient_client_opens_circuit_after_failures() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    async with ResilientAsyncClient(
        retry_policy=RetryPolicy(max_attempts=1),
        circuit_breaker_policy=CircuitBreakerPolicy(failure_threshold=1),
        transport=httpx.MockTransport(handler),
        base_url="http://test",
    ) as client:
        response = await client.get("/resource")
        with pytest.raises(CircuitOpenError):
            await client.get("/resource")

    assert response.status_code == 503
    assert attempts == 1