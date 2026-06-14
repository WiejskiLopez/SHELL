from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.entities.template_graph_node import TemplateGraphNode
    from shell_ddd.domain.value_objects.ids import TemplateGraphId


@dataclass(slots=True)
class TemplateGraph:
    id: TemplateGraphId
    name: str
    purpose: str
    nodes: list[TemplateGraphNode] = field(default_factory=list)

    def add_node(self, node: TemplateGraphNode) -> None:
        self.nodes.append(node)
        self.nodes.sort(key=lambda n: n.position)

    def remove_node(
            self,
            node_id: TemplateGraphNodeId,
    ) -> None:
        self.nodes = [
            n
            for n in self.nodes
            if n.id != node_id
        ]

    def get_node(
            self,
            position: int,
    ) -> TemplateGraphNode | None:
        return next(
            (
                n
                for n in self.nodes
                if n.position == position
            ),
            None,
        )
