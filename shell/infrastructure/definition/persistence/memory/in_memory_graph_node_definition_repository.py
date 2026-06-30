from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
    GraphNodeDefinition,
)
from shell.domain.definition.aggregates.graph_node_definition.repositories import (
    GraphNodeDefinitionRepository,
)
from shell.domain.definition.aggregates.graph_node_definition.value_objects import (
    GraphNodeDefinitionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects import (
        GraphDefinitionId,
    )


class InMemoryGraphNodeDefinitionRepository(
    InMemoryRepository[GraphNodeDefinition, GraphNodeDefinitionId], GraphNodeDefinitionRepository
):
    async def save(self, node: GraphNodeDefinition) -> None:
        self._store[node.id.value] = node

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeDefinition]:
        return [
            node for node in self._store.values() if node.graph_definition_id == graph_definition_id
        ]
