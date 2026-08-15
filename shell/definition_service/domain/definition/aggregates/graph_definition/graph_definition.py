from __future__ import annotations

from shell.definition_service.domain.definition.aggregates.graph_definition.events.graph_definition_changed_event import (
    GraphDefinitionChangedEvent,
)
from shell.definition_service.domain.definition.aggregates.graph_definition.events.graph_definition_created_event import (
    GraphDefinitionCreatedEvent,
)
from shell.definition_service.domain.definition.aggregates.graph_definition.events.graph_definition_deleted_event import (
    GraphDefinitionDeletedEvent,
)
from shell.definition_service.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt


class GraphDefinition(AggregateRoot[GraphDefinitionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
    )

    _created_at: CreatedAt
    _changed_at: ChangedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        *,
        id: GraphDefinitionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
    ) -> None:
        super().__init__(id)
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        id: GraphDefinitionId,
        now: CreatedAt,
    ) -> GraphDefinition:
        return cls._new(id=id, now=OccurredAt.from_datetime(now.value))

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionChangedEvent.now(
                graph_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionDeletedEvent.now(
                graph_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @classmethod
    def restore(
        cls,
        *,
        id: GraphDefinitionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
    ) -> GraphDefinition:
        return cls(
            id=id,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(
        cls,
        id: GraphDefinitionId,
        now: OccurredAt,
    ) -> GraphDefinition:
        instance = cls(
            id=id,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            GraphDefinitionCreatedEvent.now(
                graph_definition_id=id,
                now=now,
            )
        )
        return instance
