from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.entities.graph_node_definition import GraphNodeDefinition
    from shell.domain.value_objects.ids import GraphNodeDefinitionId


class GraphNodeDefinitionRepository(Protocol):
    async def get_by_id(
        self, graph_node_execution_id: GraphNodeDefinitionId
    ) -> GraphNodeDefinition | None: ...

    async def save(self, node: GraphNodeDefinition) -> None: ...
