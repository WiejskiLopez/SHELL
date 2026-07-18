from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.domain.definition.aggregates.node_link_definition.events.node_link_definition_created_event import NodeLinkDefinitionCreatedEvent
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from definition.aggregates.node_link_definition.events.nodelinkdefinition_updated_event import NodeLinkDefinitionUpdatedEvent
from definition.aggregates.node_link_definition.events.nodelinkdefinition_deleted_event import NodeLinkDefinitionDeletedEvent

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )

class NodeLinkDefinition(AggregateRoot[NodeLinkDefinitionId]):
    __slots__ = (
        "_updated_at",
        "_created_at",
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
    def _new(
        cls,
        *,
        id_: NodeLinkDefinitionId,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
    ) -> NodeLinkDefinition:
        instance = cls(
            id=id_,
            graph_definition_id=graph_definition_id,
            node_definition_id=node_definition_id,
        )
        instance.append_event(
            NodeLinkDefinitionCreatedEvent.now(
                nodelinkdefinition_id=instance.id,
                now=now,
            )
        )
        return instance
    @classmethod
    def create(
        cls,
        *,
        id_: NodeLinkDefinitionId,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
    ) -> NodeLinkDefinition:
        return cls._new(id_=id_, graph_definition_id=graph_definition_id, node_definition_id=node_definition_id, now=now)

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

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            NodeLinkDefinitionDeletedEvent.now(
                nodelinkdefinition_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            NodeLinkDefinitionUpdatedEvent.now(
                nodelinkdefinition_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def node_definition_id(self) -> NodeDefinitionId:
        return self._node_definition_id
