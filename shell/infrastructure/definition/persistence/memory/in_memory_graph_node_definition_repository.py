from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.graph_definition_repository import (
    GraphNodeDefinitionRepository,
)

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
    from shell.domain.definition.value_objects.ids import GraphDefinitionId, GraphNodeDefinitionId


class InMemoryGraphNodeDefinitionRepository(GraphNodeDefinitionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphNodeDefinition] = {}

    async def get_by_id(
        self, graph_node_execution_id: GraphNodeDefinitionId
    ) -> GraphNodeDefinition | None:
        return self._store.get(graph_node_execution_id.value)

    async def save(self, node: GraphNodeDefinition, graph_definition_id: GraphDefinitionId) -> None:
        self._store[node.id.value] = node
