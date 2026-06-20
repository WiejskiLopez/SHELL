from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.ports.definition_provider import DefinitionProvider
from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,
    GraphNodeExecutionDefinition,
)

if TYPE_CHECKING:
    from shell.application.definition.dto.graph_definition import GraphDefinitionDto
    from shell.application.definition.ports.queries.graph_definition_query_service import (
        GraphDefinitionQueryService,
    )


class DefinitionProviderAdapter(DefinitionProvider):
    def __init__(self, query_service: GraphDefinitionQueryService) -> None:
        self._query_service = query_service

    async def get_graph_definition(self, definition_id: str) -> GraphExecutionDefinition | None:
        dto = await self._query_service.get_graph_definition(definition_id)
        if dto is None:
            return None
        return self._map_to_execution(dto)

    async def get_graph_definition_by_name(self, name: str) -> GraphExecutionDefinition | None:
        dto = await self._query_service.get_graph_definition_by_name(name)
        if dto is None:
            return None
        return self._map_to_execution(dto)

    def _map_to_execution(self, dto: GraphDefinitionDto) -> GraphExecutionDefinition:
        return GraphExecutionDefinition(
            id=dto.id,
            name=dto.name,
            graph_node_execution_definitions=[
                GraphNodeExecutionDefinition(
                    position=nd.position,
                    mode=nd.mode,
                    role=nd.role,
                    node_type=nd.node_type,
                    model=nd.model,
                    command=nd.command,
                    timeout=nd.timeout,
                    retries=nd.retries,
                    log_level=nd.log_level,
                    max_step=nd.max_step,
                    no_ask_user=nd.no_ask_user,
                    autopilot=nd.autopilot,
                    status_initial=nd.status_initial,
                    extra=dict(nd.extra),
                    script=nd.script,
                    script_type=nd.script_type,
                )
                for nd in dto.graph_node_definitions
            ],
        )
