from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition.events.graph_definition_created_event import (
    GraphDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from definition.aggregates.graph_definition.events.graphdefinition_updated_event import GraphDefinitionUpdatedEvent
from definition.aggregates.graph_definition.events.graphdefinition_deleted_event import GraphDefinitionDeletedEvent

from shell.platform.domain.value_objects.deletedat import DeletedAt

from shell.platform.domain.value_objects.updatedat import UpdatedAt

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.created_at import CreatedAt


class GraphDefinition(AggregateRoot[GraphDefinitionId]):
    __slots__ = (
        "_updated_at",
        "_created_at",)

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
                    now=now,
                )
            )

        return instance

    @classmethod
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            GraphDefinitionUpdatedEvent.now(
                graphdefinition_id=self._id,
                now=now,
            )
        )





    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionDeletedEvent.now(
                graphdefinition_id=self._id,
                now=CreatedAt.from_datetime(now.value),
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
        now: CreatedAt | None = None,
    ) -> GraphDefinition:
        instance = cls(id=id)

        if now is not None:
            instance.append_event(
                GraphDefinitionCreatedEvent.now(
                    graph_definition_id=id,
                    now=now,
                )
            )

        return instance

    @classmethod
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            GraphDefinitionUpdatedEvent.now(
                graphdefinition_id=self._id,
                now=now,
            )
        )





    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            GraphDefinitionDeletedEvent.now(
                graphdefinition_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
