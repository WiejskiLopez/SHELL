from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition.events.graph_definition_created_event import (
    GraphDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.graph_definition.events.graph_definition_deleted_event import (
    GraphDefinitionDeletedEvent,
)
from shell.domain.definition.aggregates.graph_definition.events.graph_definition_updated_event import (
    GraphDefinitionUpdatedEvent,
)
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class GraphDefinition(AggregateRoot[GraphDefinitionId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    def __init__(
        self,
        id: GraphDefinitionId,
    ) -> None:
        super().__init__(id)

    @classmethod
    def create(
        cls,
        id: GraphDefinitionId,
        now: CreatedAt | None = None,
    ) -> GraphDefinition:
        instance = cls(id=id)

        if now is not None:
            instance.append_event(
                GraphDefinitionCreatedEvent.now(
                    graph_definition_id=id,
                    now=OccurredAt.from_datetime(now.value),
                )
            )

        return instance

    def _update(self, now: CreatedAt) -> None:
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionUpdatedEvent.now(
                graph_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionDeletedEvent.now(
                graph_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @classmethod
    def restore(
        cls,
        id: GraphDefinitionId,
    ) -> GraphDefinition:
        return cls(id=id)

    @classmethod
    def _new(
        cls,
        id: GraphDefinitionId,
        now: OccurredAt | None = None,
    ) -> GraphDefinition:
        instance = cls(id=id)

        if now is not None:
            instance.append_event(
                GraphDefinitionCreatedEvent.now(
                    graph_definition_id=id,
                    now=OccurredAt.from_datetime(now.value),
                )
            )

        return instance
