from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.entities.graph_definition import GraphDefinition
    from shell.domain.entities.graph_definition_node import GraphDefinitionNode
    from shell.domain.value_objects.ids import GraphDefinitionId, GraphDefinitionNodeId


class GraphDefinitionRepository(Protocol):
    async def get(self, graph_id: GraphDefinitionId) -> GraphDefinition | None: ...

    async def get_graph_definition_by_name(
        self, graph_definition_by_name: str
    ) -> GraphDefinition | None: ...

    async def save(self, graph: GraphDefinition) -> None: ...


class GraphDefinitionNodeRepository(Protocol):
    async def get_by_id(self, node_id: GraphDefinitionNodeId) -> GraphDefinitionNode | None: ...

    async def save(self, node: GraphDefinitionNode) -> None: ...
