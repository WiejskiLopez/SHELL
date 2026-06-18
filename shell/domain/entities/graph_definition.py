from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.entities.graph_node_definition import GraphNodeDefinition
    from shell.domain.value_objects.ids import GraphDefinitionId, GraphNodeDefinitionId


@dataclass(slots=True)
class GraphDefinition:
    id: GraphDefinitionId
    name: str
    purpose: str
    graph_node_definitions: list[GraphNodeDefinition] = field(default_factory=list)

    def add_graph_node_definition(self, node: GraphNodeDefinition) -> None:
        self.graph_node_definitions.append(node)
        self.graph_node_definitions.sort(key=lambda n: n.position)

    def remove_graph_node_definition(
        self,
        graph_node_definition_id: GraphNodeDefinitionId,
    ) -> None:
        self.graph_node_definitions = [graph_node_definition for graph_node_definition in self.graph_node_definitions if graph_node_definition.id != graph_node_definition_id]

    def get_graph_node_definition(
        self,
        position: int,
    ) -> GraphNodeDefinition | None:
        return next(
            (graph_node_definition for graph_node_definition in self.graph_node_definitions if graph_node_definition.position == position),
            None,
        )
