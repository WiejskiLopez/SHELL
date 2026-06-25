from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
    from shell.domain.definition.value_objects.ids import GraphDefinitionId, GraphNodeDefinitionId


class GraphNodeDefinitionRepository(Protocol):
    async def get_by_id(self, graph_node_execution_id: GraphNodeDefinitionId) -> GraphNodeDefinition | None: ...
    async def save(self, node: GraphNodeDefinition, graph_definition_id: GraphDefinitionId) -> None: ...
    async def delete(self, id: GraphNodeDefinitionId) -> None: ...
    async def exists(self, id: GraphNodeDefinitionId) -> bool: ...
