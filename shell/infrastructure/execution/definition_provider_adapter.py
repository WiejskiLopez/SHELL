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
        graph_definition_dto = await self._query_service.get_graph_definition(definition_id)
        if graph_definition_dto is None:
            return None
        return self._map_to_execution(graph_definition_dto)

    async def get_graph_definition_by_name(self, name: str) -> GraphExecutionDefinition | None:
        graph_definition_dto = await self._query_service.get_graph_definition_by_name(name)
        if graph_definition_dto is None:
            return None
        return self._map_to_execution(graph_definition_dto)

    def _map_to_execution(self, graph_definition_dto: GraphDefinitionDto) -> GraphExecutionDefinition:
        return GraphExecutionDefinition(
            id=graph_definition_dto.id,
            name=graph_definition_dto.name,
            graph_node_execution_definitions=[
                GraphNodeExecutionDefinition(
                    position=graph_node_definition.position,
                    mode=graph_node_definition.mode,
                    role=graph_node_definition.role,
                    node_type=graph_node_definition.node_type,
                    model=graph_node_definition.model,
                    command=graph_node_definition.command,
                    timeout=graph_node_definition.timeout,
                    retries=graph_node_definition.retries,
                    log_level=graph_node_definition.log_level,
                    max_step=graph_node_definition.max_step,
                    no_ask_user=graph_node_definition.no_ask_user,
                    autopilot=graph_node_definition.autopilot,
                    status_initial=graph_node_definition.status_initial,
                    extra=dict(graph_node_definition.extra),
                    script=graph_node_definition.script,
                    script_type=graph_node_definition.script_type,
                )
                for graph_node_definition in graph_definition_dto.graph_node_definitions
            ],
        )
