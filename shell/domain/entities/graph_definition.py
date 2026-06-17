from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.entities.graph_definition_node import GraphDefinitionNode
    from shell.domain.value_objects.ids import GraphDefinitionId, GraphDefinitionNodeId


@dataclass(slots=True)
class GraphDefinition:
    id: GraphDefinitionId
    name: str
    purpose: str
    nodes: list[GraphDefinitionNode] = field(default_factory=list)

    def add_node(self, node: GraphDefinitionNode) -> None:
        self.nodes.append(node)
        self.nodes.sort(key=lambda n: n.position)

    def remove_node(
        self,
        node_id: GraphDefinitionNodeId,
    ) -> None:
        self.nodes = [n for n in self.nodes if n.id != node_id]

    def get_node(
        self,
        position: int,
    ) -> GraphDefinitionNode | None:
        return next(
            (n for n in self.nodes if n.position == position),
            None,
        )
