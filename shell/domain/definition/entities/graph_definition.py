from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.base.entity import Entity
from shell.domain.platform.value_objects.ids import GraphDefinitionId, GraphNodeDefinitionId

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
    from shell.domain.definition.entities.graph_node_transition_definition import (
        GraphNodeTransitionDefinition,
    )


class GraphDefinition(Entity[GraphDefinitionId]):
    __slots__ = ("name", "purpose", "graph_node_definitions", "_transition_definitions")

    def __init__(
        self,
        id: GraphDefinitionId,
        name: str,
        purpose: str,
        graph_node_definitions: list[GraphNodeDefinition] | None = None,
        transition_definitions: list[GraphNodeTransitionDefinition] | None = None,
    ) -> None:
        super().__init__(id)
        self.name = name
        self.purpose = purpose
        self.graph_node_definitions = graph_node_definitions or []
        self._transition_definitions = list(transition_definitions) if transition_definitions else []

    @property
    def transition_definitions(self) -> tuple[GraphNodeTransitionDefinition, ...]:
        return tuple(self._transition_definitions)

    def add_graph_node_definition(self, node: GraphNodeDefinition) -> None:
        self.graph_node_definitions.append(node)
        self.graph_node_definitions.sort(key=lambda n: n.position)

    def remove_graph_node_definition(
        self,
        graph_node_definition_id: GraphNodeDefinitionId,
    ) -> None:
        self.graph_node_definitions = [
            graph_node_definition
            for graph_node_definition in self.graph_node_definitions
            if graph_node_definition.id != graph_node_definition_id
        ]

    def get_graph_node_definition(
        self,
        position: int,
    ) -> GraphNodeDefinition | None:
        return next(
            (
                graph_node_definition
                for graph_node_definition in self.graph_node_definitions
                if graph_node_definition.position == position
            ),
            None,
        )

    def add_transition_definition(self, transition: GraphNodeTransitionDefinition) -> None:
        self._transition_definitions.append(transition)
