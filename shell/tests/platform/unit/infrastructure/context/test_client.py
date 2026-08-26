from __future__ import annotations

import httpx
import pytest

from shell.platform.infrastructure.context.client import CorrelationIdAsyncClient


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