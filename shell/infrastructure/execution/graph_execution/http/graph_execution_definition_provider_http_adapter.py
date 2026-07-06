from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_definition_provider import (
    GraphExecutionDefinitionProvider,
)
from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,
    NodeExecutionDefinition,
)

if TYPE_CHECKING:
    import httpx

    from shell.domain.execution.aggregates.graph_execution.ports.graph_definition_semantic_query import (
        GraphDefinitionSemanticQuery,
    )


class GraphExecutionDefinitionProviderHttpAdapter(GraphExecutionDefinitionProvider):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_graph_definition(self, definition_id: str) -> GraphExecutionDefinition | None:
        response = await self._client.get(f"/api/v1/definitions/{definition_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return self._map_to_execution(data)

    async def get_graph_definition_by_semantic_name(
        self,
        query: GraphDefinitionSemanticQuery,
    ) -> GraphExecutionDefinition | None:
        payload = query.to_payload()
        response = await self._client.post("/api/v1/definitions/by-semantic-name", json=payload)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return self._map_to_execution(data)

    @staticmethod
    def _map_to_execution(data: dict[str, Any]) -> GraphExecutionDefinition:
        return GraphExecutionDefinition(
            id=data["id"],
            node_execution_definitions=[
                NodeExecutionDefinition(
                    mode=node["mode"],
                    role=node["role"],
                    node_type=node["node_type"],
                    max_step=node.get("max_step"),
                )
                for node in data.get("node_definitions", [])
            ],
        )
