from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

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


class TestGraphDefinitionProviderHttpAdapter:
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        return AsyncMock(spec="httpx.AsyncClient")

    @pytest.fixture
    def adapter(self, mock_client: AsyncMock) -> GraphDefinitionProviderHttpAdapter:
        return GraphDefinitionProviderHttpAdapter(client=mock_client)

    async def test_get_definition_returns_none_on_404(
        self,
        adapter: GraphDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(return_value=Mock(status_code=404))
        result = await adapter.get_graph_definition(GraphDefinitionIdRef("nonexistent-id"))
        assert result is None
        mock_client.get.assert_awaited_once_with("/api/v1/graph-definitions/nonexistent-id")

    async def test_get_definition_maps_response(
        self,
        adapter: GraphDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        response_data = {
            "id": "def-123",
            "created_at": "2026-08-13T12:00:00+00:00",
        }
        mock_client.get = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value=response_data))
        )
        result = await adapter.get_graph_definition(GraphDefinitionIdRef("def-123"))
        assert isinstance(result, GraphDefinitionReference)
        assert result.graph_definition_id == GraphDefinitionIdRef("def-123")

    async def test_get_definition_by_semantic(
        self,
        adapter: GraphDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        query = GraphDefinitionSemanticQuery(text="find me", purpose="planning")
        response_data: dict[str, Any] = {
            "id": "def-456",
            "created_at": "2026-08-13T12:00:00+00:00",
        }
        mock_client.post = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value=response_data))
        )
        result = await adapter.get_graph_definition_by_semantic(query)
        assert isinstance(result, GraphDefinitionReference)
        assert result.graph_definition_id == GraphDefinitionIdRef("def-456")
        mock_client.post.assert_awaited_once_with(
            "/api/v1/graph-definitions/by-semantic",
            json=query.to_payload(),
        )

    async def test_get_definition_by_semantic_returns_none_on_404(
        self,
        adapter: GraphDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        query = GraphDefinitionSemanticQuery(text="nothing")
        mock_client.post = AsyncMock(return_value=Mock(status_code=404))
        result = await adapter.get_graph_definition_by_semantic(query)
        assert result is None

    async def test_raises_on_5xx(
        self,
        adapter: GraphDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(
            return_value=Mock(
                status_code=500, raise_for_status=Mock(side_effect=Exception("Server error"))
            )
        )
        with pytest.raises(Exception, match="Server error"):
            await adapter.get_graph_definition(GraphDefinitionIdRef("def-123"))
