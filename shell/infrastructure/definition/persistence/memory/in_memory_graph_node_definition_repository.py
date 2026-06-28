from __future__ import annotations

from shell.domain.definition.repositories.graph_definition_repository import (
    GraphNodeDefinitionRepository,
)
from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
from shell.domain.definition.value_objects.ids import GraphDefinitionId, GraphNodeDefinitionId
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryGraphNodeDefinitionRepository(InMemoryRepository[GraphNodeDefinition, GraphNodeDefinitionId], GraphNodeDefinitionRepository):

    async def save(self, node: GraphNodeDefinition, graph_definition_id: GraphDefinitionId) -> None:
        self._store[node.id.value] = node
