from __future__ import annotations

from shell.definition_service.domain.definition.aggregates.node_definition.events.node_definition_changed_event import (
    NodeDefinitionChangedEvent,
)
from shell.definition_service.domain.definition.aggregates.node_definition.events.node_definition_created_event import (
    NodeDefinitionCreatedEvent,
)
from shell.definition_service.domain.definition.aggregates.node_definition.events.node_definition_deleted_event import (
    NodeDefinitionDeletedEvent,
)
from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.max_step import (
    MaxStep,
)
from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.node_type import (
    NodeType,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt


class NodeDefinition(AggregateRoot[NodeDefinitionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_node_type",
        "_max_step",
    )

    def __init__(
        self,
        id: NodeDefinitionId,
        *,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        node_type: NodeType,
        max_step: MaxStep | None = None,
    ) -> None:
        super().__init__(id)
        self._node_type = node_type if isinstance(node_type, NodeType) else NodeType(node_type)
        self._max_step = (
            max_step if max_step is None or isinstance(max_step, MaxStep) else MaxStep(max_step)
        )
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        id: NodeDefinitionId,
        now: CreatedAt,
        node_type: NodeType,
        max_step: MaxStep | None = None,
    ) -> NodeDefinition:
        return cls._new(
            id=id,
            node_type=node_type,
            max_step=max_step,
            now=OccurredAt.from_datetime(now.value),
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            NodeDefinitionChangedEvent.now(
                node_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            NodeDefinitionDeletedEvent.now(
                node_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def node_type(self) -> NodeType:
        return self._node_type

    @property
    def max_step(self) -> MaxStep | None:
        return self._max_step

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    @classmethod
    def restore(
        cls,
        id: NodeDefinitionId,
        *,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        node_type: NodeType,
        max_step: MaxStep | None = None,
    ) -> NodeDefinition:
        return cls(
            id=id,
            node_type=node_type,
            max_step=max_step,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(
        cls,
        id: NodeDefinitionId,
        now: OccurredAt,
        node_type: NodeType,
        max_step: MaxStep | None = None,
    ) -> NodeDefinition:
        instance = cls(
            id=id,
            node_type=node_type,
            max_step=max_step,
            created_at=CreatedAt.from_datetime(now.value),
        )

        instance.append_event(
            NodeDefinitionCreatedEvent.now(
                node_definition_id=id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

        return instance
