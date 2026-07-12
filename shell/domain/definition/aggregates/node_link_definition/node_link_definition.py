from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )


class NodeLinkDefinition(AggregateRoot[NodeLinkDefinitionId]):
    __slots__ = (
        "_graph_definition_id",
        "_node_definition_id",
    )

    def __init__(
        self,
        id: NodeLinkDefinitionId,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
    ) -> None:
        super().__init__(id)
        self._graph_definition_id = graph_definition_id
        self._node_definition_id = node_definition_id

    @classmethod
    def create(
        cls,
        *,
        id_: NodeLinkDefinitionId,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
    ) -> NodeLinkDefinition:
        return cls(
            id=id_,
            graph_definition_id=graph_definition_id,
            node_definition_id=node_definition_id,
        )

    @classmethod
    def restore(
        cls,
        id: NodeLinkDefinitionId,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
    ) -> Self:
        return cls(
            id=id,
            graph_definition_id=graph_definition_id,
            node_definition_id=node_definition_id,
        )

    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def node_definition_id(self) -> NodeDefinitionId:
        return self._node_definition_id
