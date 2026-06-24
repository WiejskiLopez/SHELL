from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.value_objects.ids import GraphDefinitionId, GraphNodeDefinitionId
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
    from shell.domain.definition.entities.graph_node_transition_definition import (
        GraphNodeTransitionDefinition,
    )


class GraphDefinition(Entity[GraphDefinitionId]):
    __slots__ = ("_name", "_purpose", "_graph_node_definitions", "_transition_definitions")

    def __init__(
        self,
        id: GraphDefinitionId,
        name: str,
        purpose: str,
        graph_node_definitions: list[GraphNodeDefinition] | None = None,
        transition_definitions: list[GraphNodeTransitionDefinition] | None = None,
    ) -> None:
        super().__init__(id)
        self._name = name
        self._purpose = purpose
        self._graph_node_definitions = list(graph_node_definitions) if graph_node_definitions else []
        self._transition_definitions = (
            list(transition_definitions) if transition_definitions else []
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def purpose(self) -> str:
        return self._purpose

    @property
    def graph_node_definitions(self) -> tuple[GraphNodeDefinition, ...]:
        return tuple(self._graph_node_definitions)

    @property
    def transition_definitions(self) -> tuple[GraphNodeTransitionDefinition, ...]:
        return tuple(self._transition_definitions)

    def add_graph_node_definition(self, node: GraphNodeDefinition) -> None:
        self._graph_node_definitions.append(node)
        self._graph_node_definitions.sort(key=lambda n: n.position)

    def remove_graph_node_definition(
        self,
        graph_node_definition_id: GraphNodeDefinitionId,
    ) -> None:
        self._graph_node_definitions = [
            graph_node_definition
            for graph_node_definition in self._graph_node_definitions
            if graph_node_definition.id != graph_node_definition_id
        ]

    def get_graph_node_definition(
        self,
        position: int,
    ) -> GraphNodeDefinition | None:
        return next(
            (
                graph_node_definition
                for graph_node_definition in self._graph_node_definitions
                if graph_node_definition.position == position
            ),
            None,
        )

    def add_transition_definition(self, transition: GraphNodeTransitionDefinition) -> None:
        self._transition_definitions.append(transition)
