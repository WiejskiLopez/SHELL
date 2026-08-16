from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.graph_execution.ports.graph_definition_provider import (
    GraphDefinitionProvider,
)
from shell.execution_service.infrastructure.execution.graph_execution.adapters.graph_definition.contracts.v1.graph_definition_response import (
    GraphDefinitionResponseV1,
)
from shell.execution_service.infrastructure.execution.graph_execution.adapters.graph_definition.mappers.graph_definition_response_to_domain import (
    graph_definition_response_to_domain,
)

if TYPE_CHECKING:
    import httpx

    from shell.execution_service.domain.execution.aggregates.graph_execution.ports.graph_definition_semantic_query import (
        GraphDefinitionSemanticQuery,
    )
    from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
        GraphDefinitionIdRef,
    )
    from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_reference import (
        GraphDefinitionReference,
    )


class GraphDefinitionProviderHttpAdapter(GraphDefinitionProvider):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_graph_definition(
        self, definition_id: GraphDefinitionIdRef
    ) -> GraphDefinitionReference | None:
        response = await self._client.get(f"/api/v1/graph-definitions/{definition_id.value}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return graph_definition_response_to_domain(
            GraphDefinitionResponseV1.model_validate(response.json())
        )

    async def get_graph_definition_by_semantic(
        self,
        query: GraphDefinitionSemanticQuery,
    ) -> GraphDefinitionReference | None:
        payload = query.to_payload()
        response = await self._client.post("/api/v1/graph-definitions/by-semantic", json=payload)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return graph_definition_response_to_domain(
            GraphDefinitionResponseV1.model_validate(response.json())
        )
