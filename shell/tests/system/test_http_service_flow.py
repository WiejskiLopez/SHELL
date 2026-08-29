"""System tests — real HTTP flow between Execution and Definition bounded contexts.

Proves the cross-service contract over actual HTTP (ASGI) instead of in-process
handler calls:

  Execution (GraphDefinitionProviderHttpAdapter + ResilientAsyncClient)
      → HTTP /api/v1/graph-definitions/* with X-API-Key + X-Correlation-ID
      → Definition (FastAPI app, AuthMiddleware, query handlers → own DB)

Scenarios: 200 mapping, 404 → None, 401 without/with key, 503 retry then circuit
breaker opens, no retry for POST, correlation-id propagation. Uses two isolated
SQLite databases — no shared container.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from shell.definition_service.bootstrap.definition.container.definition_core_container import (
    DefinitionCoreContainer,
    configure_definition_container,
)
from shell.definition_service.framework.definition.api.app import create_definition_app
from shell.definition_service.infrastructure.definition.seed import bootstrap_definition_database
from shell.execution_service.domain.execution.aggregates.graph_execution.ports.graph_definition_semantic_query import (
    GraphDefinitionSemanticQuery,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
    GraphDefinitionIdRef,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_reference import (
    GraphDefinitionReference,
)
from shell.execution_service.infrastructure.execution.graph_execution.adapters.graph_definition.graph_definition_provider_http_adapter import (
    GraphDefinitionProviderHttpAdapter,
)
from shell.platform.application.context.correlation_id import (
    reset_correlation_id,
    set_correlation_id,
)
from shell.platform.infrastructure.context.client import ResilientAsyncClient
from shell.platform.infrastructure.context.resilience import (
    CircuitBreakerPolicy,
    CircuitOpenError,
    RetryPolicy,
)
from shell.tests.shared.sql_lifecycle import track_session_factory

if TYPE_CHECKING:
    from fastapi import FastAPI

BASE_GRAPH_ID = "base-planner-id"
DEFINITION_API_KEY = "definition-flow-key"
GET_ID = GraphDefinitionIdRef(BASE_GRAPH_ID)
GRAPH_PAYLOAD: dict[str, str] = {
    "id": "def-123",
    "created_at": "2026-08-13T12:00:00+00:00",
}


class _FakeDefinitionApp:
    """Minimal ASGI app that mimics the Definition contract (200 or 503, records headers)."""

    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.requests: list[dict[str, str]] = []

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        self.requests.append(
            {key.decode(): value.decode() for key, value in scope.get("headers", [])}
        )
        while True:
            message = await receive()
            if message["type"] == "http.request" and not message.get("more_body"):
                break
        body: bytes
        if self.status == 200:
            body = json.dumps(GRAPH_PAYLOAD).encode("utf-8")
        else:
            body = b'{"detail":"definition unavailable"}'
        await send(
            {
                "type": "http.response.start",
                "status": self.status,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": body})


async def _make_definition_app(tmp_path) -> FastAPI:
    """Definition BC app with its own database seeded with the base planner graph."""
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'definition-flow.db'}"
    await bootstrap_definition_database(db_url)
    container = DefinitionCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_definition_container(container)
    track_session_factory(container.session_factory())
    return create_definition_app(container, api_key=DEFINITION_API_KEY)


def _provider(
    transport_app: Any,
    *,
    api_key: str = DEFINITION_API_KEY,
    retry_policy: RetryPolicy | None = None,
    circuit_breaker_policy: CircuitBreakerPolicy | None = None,
) -> ResilientAsyncClient:
    return ResilientAsyncClient(
        transport=ASGITransport(app=transport_app),
        base_url="http://definition",
        service_api_key=api_key,
        retry_policy=retry_policy or RetryPolicy(max_attempts=1),
        circuit_breaker_policy=circuit_breaker_policy or CircuitBreakerPolicy(),
    )


class TestHttpFlowExecutionToDefinition:
    async def test_successful_flow_returns_domain_reference(self, tmp_path) -> None:
        definition_app = await _make_definition_app(tmp_path)
        async with _provider(definition_app) as client:
            provider = GraphDefinitionProviderHttpAdapter(client)
            reference = await provider.get_graph_definition(GET_ID)

        assert isinstance(reference, GraphDefinitionReference)
        assert reference.graph_definition_id == GET_ID

    async def test_not_found_maps_to_none(self, tmp_path) -> None:
        definition_app = await _make_definition_app(tmp_path)
        async with _provider(definition_app) as client:
            provider = GraphDefinitionProviderHttpAdapter(client)
            reference = await provider.get_graph_definition(GraphDefinitionIdRef("does-not-exist"))

        assert reference is None

    async def test_definition_rejects_missing_api_key(self, tmp_path) -> None:
        definition_app = await _make_definition_app(tmp_path)
        async with AsyncClient(
            transport=ASGITransport(app=definition_app), base_url="http://definition"
        ) as client:
            without_key = await client.get("/api/v1/graph-definitions/base-planner-id")
            with_key = await client.get(
                "/api/v1/graph-definitions/base-planner-id",
                headers={"X-API-Key": DEFINITION_API_KEY},
            )

        assert without_key.status_code == 401
        assert with_key.status_code == 200

    async def test_unauthenticated_caller_is_rejected_by_downstream_service(self, tmp_path) -> None:
        definition_app = await _make_definition_app(tmp_path)
        async with _provider(definition_app, api_key="") as client:
            provider = GraphDefinitionProviderHttpAdapter(client)
            with pytest.raises(httpx.HTTPStatusError) as error:
                await provider.get_graph_definition(GET_ID)

        assert error.value.response.status_code == 401

    async def test_get_retries_on_503_then_opens_circuit(self) -> None:
        downstream = _FakeDefinitionApp(status=503)
        retry = RetryPolicy(max_attempts=3, initial_delay=0.0, max_delay=0.0, jitter=0.0)
        breaker = CircuitBreakerPolicy(failure_threshold=1)
        async with _provider(
            downstream, retry_policy=retry, circuit_breaker_policy=breaker
        ) as client:
            provider = GraphDefinitionProviderHttpAdapter(client)

            with pytest.raises(httpx.HTTPStatusError) as error:
                await provider.get_graph_definition(GET_ID)
            assert error.value.response.status_code == 503

            with pytest.raises(CircuitOpenError):
                await provider.get_graph_definition(GET_ID)

        assert len(downstream.requests) == 3

    async def test_post_by_semantic_is_not_retried_on_503(self) -> None:
        downstream = _FakeDefinitionApp(status=503)
        retry = RetryPolicy(max_attempts=3, initial_delay=0.0, max_delay=0.0, jitter=0.0)
        async with _provider(downstream, retry_policy=retry) as client:
            provider = GraphDefinitionProviderHttpAdapter(client)
            query = GraphDefinitionSemanticQuery(text="find me", purpose="planning")

            with pytest.raises(httpx.HTTPStatusError) as error:
                await provider.get_graph_definition_by_semantic(query)

        assert error.value.response.status_code == 503
        assert len(downstream.requests) == 1

    async def test_correlation_id_propagates_to_downstream(self) -> None:
        downstream = _FakeDefinitionApp(status=200)
        token = set_correlation_id("flow-corr-123")
        try:
            async with _provider(downstream) as client:
                provider = GraphDefinitionProviderHttpAdapter(client)
                await provider.get_graph_definition(GET_ID)
        finally:
            reset_correlation_id(token)

        assert downstream.requests[0].get("x-correlation-id") == "flow-corr-123"
