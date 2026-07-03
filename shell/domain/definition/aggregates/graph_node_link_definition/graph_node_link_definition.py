from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.definition.aggregates.graph_node_link_definition.value_objects.graph_node_link_definition_id import (
    GraphNodeLinkDefinitionId,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )


class GraphNodeLinkDefinition(AggregateRoot[GraphNodeLinkDefinitionId]):
    __slots__ = (
        "_graph_definition_id",
        "_graph_node_definition_id",
    )

    def __init__(
        self,
        id: GraphNodeLinkDefinitionId,
        graph_definition_id: GraphDefinitionId,
        graph_node_definition_id: GraphNodeDefinitionId,
    ) -> None:
        super().__init__(id)
        self._graph_definition_id = graph_definition_id
        self._graph_node_definition_id = graph_node_definition_id

    @classmethod
    def restore(
        cls,
        id: GraphNodeLinkDefinitionId,
        graph_definition_id: GraphDefinitionId,
        graph_node_definition_id: GraphNodeDefinitionId,
    ) -> Self:
        return cls(
            id=id,
            graph_definition_id=graph_definition_id,
            graph_node_definition_id=graph_node_definition_id,
        )

    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def graph_node_definition_id(self) -> GraphNodeDefinitionId:
        return self._graph_node_definition_id
