from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from shell.domain.execution.aggregates.graph_execution.ports.graph_definition_semantic_query import (
    GraphDefinitionSemanticQuery,
)
from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,
)
from shell.infrastructure.execution.http.graph_execution_definition_provider_http_adapter import (
    GraphExecutionDefinitionProviderHttpAdapter,
)


class TestGraphExecutionDefinitionProviderHttpAdapter:
    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        return AsyncMock(spec="httpx.AsyncClient")

    @pytest.fixture
    def adapter(self, mock_client: AsyncMock) -> GraphExecutionDefinitionProviderHttpAdapter:
        return GraphExecutionDefinitionProviderHttpAdapter(client=mock_client)

    async def test_get_definition_returns_none_on_404(
        self,
        adapter: GraphExecutionDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(return_value=Mock(status_code=404))
        result = await adapter.get_graph_definition("nonexistent-id")
        assert result is None
        mock_client.get.assert_awaited_once_with("/api/v1/definitions/nonexistent-id")

    async def test_get_definition_maps_response(
        self,
        adapter: GraphExecutionDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        response_data = {
            "id": "def-123",
            "name": "test_definition",
            "system_role": "PLANNER",
            "graph_node_definitions": [
                {
                    "position": 0,
                    "mode": "agent",
                    "role": "planner",
                    "node_type": "agent",
                    "model": "gpt-4",
                    "command": "plan",
                    "timeout": 60,
                    "retries": 2,
                    "log_level": "INFO",
                    "max_step": 20,
                    "no_ask_user": False,
                    "autopilot": False,
                    "status_initial": "",
                    "script": "",
                    "script_type": "",
                }
            ],
        }
        mock_client.get = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value=response_data))
        )
        result = await adapter.get_graph_definition("def-123")
        assert isinstance(result, GraphExecutionDefinition)
        assert result.id == "def-123"
        assert result.name == "test_definition"
        assert result.system_role == "PLANNER"
        assert len(result.graph_node_execution_definitions) == 1
        node = result.graph_node_execution_definitions[0]
        assert node.position == 0
        assert node.mode == "agent"
        assert node.timeout == 60

    async def test_get_definition_by_semantic_name(
        self,
        adapter: GraphExecutionDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        query = GraphDefinitionSemanticQuery(text="find me", purpose="planning")
        response_data: dict[str, Any] = {
            "id": "def-456",
            "name": "semantic_match",
            "system_role": None,
            "graph_node_definitions": [],
        }
        mock_client.post = AsyncMock(
            return_value=Mock(status_code=200, json=Mock(return_value=response_data))
        )
        result = await adapter.get_graph_definition_by_semantic_name(query)
        assert isinstance(result, GraphExecutionDefinition)
        assert result.id == "def-456"
        mock_client.post.assert_awaited_once_with(
            "/api/v1/definitions/by-semantic-name",
            json=query.to_payload(),
        )

    async def test_get_definition_by_semantic_name_returns_none_on_404(
        self,
        adapter: GraphExecutionDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        query = GraphDefinitionSemanticQuery(text="nothing")
        mock_client.post = AsyncMock(return_value=Mock(status_code=404))
        result = await adapter.get_graph_definition_by_semantic_name(query)
        assert result is None

    async def test_raises_on_5xx(
        self,
        adapter: GraphExecutionDefinitionProviderHttpAdapter,
        mock_client: AsyncMock,
    ) -> None:
        mock_client.get = AsyncMock(
            return_value=Mock(
                status_code=500, raise_for_status=Mock(side_effect=Exception("Server error"))
            )
        )
        with pytest.raises(Exception, match="Server error"):
            await adapter.get_graph_definition("def-123")
