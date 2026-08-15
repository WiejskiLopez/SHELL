from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.definition_service.domain.definition.aggregates.node_link_definition.events.node_link_definition_changed_event import (
    NodeLinkDefinitionChangedEvent,
)
from shell.definition_service.domain.definition.aggregates.node_link_definition.events.node_link_definition_created_event import (
    NodeLinkDefinitionCreatedEvent,
)
from shell.definition_service.domain.definition.aggregates.node_link_definition.events.node_link_definition_deleted_event import (
    NodeLinkDefinitionDeletedEvent,
)
from shell.definition_service.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )


class NodeLinkDefinition(AggregateRoot[NodeLinkDefinitionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_graph_definition_id",
        "_node_definition_id",
    )

    def __init__(
        self,
        id: NodeLinkDefinitionId,
        *,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
    ) -> None:
        super().__init__(id)
        self._graph_definition_id = graph_definition_id
        self._node_definition_id = node_definition_id
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def _new(
        cls,
        *,
        id_: NodeLinkDefinitionId,
        now: OccurredAt,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
    ) -> NodeLinkDefinition:
        instance = cls(
            id=id_,
            graph_definition_id=graph_definition_id,
            node_definition_id=node_definition_id,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            NodeLinkDefinitionCreatedEvent.now(
                node_link_definition_id=instance.id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    @classmethod
    def create(
        cls,
        *,
        id_: NodeLinkDefinitionId,
        now: CreatedAt,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
    ) -> NodeLinkDefinition:
        return cls._new(
            id_=id_,
            graph_definition_id=graph_definition_id,
            node_definition_id=node_definition_id,
            now=OccurredAt.from_datetime(now.value),
        )

    @classmethod
    def restore(
        cls,
        id: NodeLinkDefinitionId,
        *,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
    ) -> Self:
        return cls(
            id=id,
            graph_definition_id=graph_definition_id,
            node_definition_id=node_definition_id,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            NodeLinkDefinitionDeletedEvent.now(
                node_link_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            NodeLinkDefinitionChangedEvent.now(
                node_link_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def node_definition_id(self) -> NodeDefinitionId:
        return self._node_definition_id

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at
