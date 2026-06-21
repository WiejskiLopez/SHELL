from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.graph_definition_repository import (
    GraphNodeDefinitionRepository,
)
from shell.domain.definition.value_objects.ids import (
    GraphNodeDefinitionId,  # noqa: TC002 — GraphNodeDefinitionId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition


class InMemoryGraphNodeDefinitionRepository(GraphNodeDefinitionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphNodeDefinition] = {}

    async def get_by_id(
        self, graph_node_execution_id: GraphNodeDefinitionId
    ) -> GraphNodeDefinition | None:
        return self._store.get(graph_node_execution_id.value)

    async def save(self, node: GraphNodeDefinition) -> None:
        self._store[node.id.value] = node
