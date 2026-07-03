from __future__ import annotations

from typing import TYPE_CHECKING

from shell.process.execution.graph_execution_saga.ports.graph_definition_node_provider import (
    GraphDefinitionNodeProvider,
    NodeDefinitionData,
)

if TYPE_CHECKING:
    import httpx


class GraphDefinitionNodeProviderHttpAdapter(GraphDefinitionNodeProvider):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_node_definitions(self, graph_definition_id: str) -> list[NodeDefinitionData]:
        response = await self._client.get(
            f"/api/v1/definitions/{graph_definition_id}/nodes",
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        return [
            NodeDefinitionData(
                node_id=node["id"],
                position=node["position"],
                role=node["role"],
                mode=node["mode"],
                node_type=node["node_type"],
            )
            for node in data
        ]
