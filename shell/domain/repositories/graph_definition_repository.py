from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.entities.graph_definition import GraphDefinition
    from shell.domain.entities.graph_node_definition import GraphNodeDefinition
    from shell.domain.value_objects.ids import GraphDefinitionId, GraphNodeDefinitionId


class GraphDefinitionRepository(Protocol):
    async def get(self, graph_execution_id: GraphDefinitionId) -> GraphDefinition | None: ...

    async def get_graph_definition_by_name(
        self, graph_definition_by_name: str
    ) -> GraphDefinition | None: ...

    async def save(self, graph: GraphDefinition) -> None: ...


class GraphNodeDefinitionRepository(Protocol):
    async def get_by_id(self, graph_node_execution_id: GraphNodeDefinitionId) -> GraphNodeDefinition | None: ...

    async def save(self, node: GraphNodeDefinition) -> None: ...
