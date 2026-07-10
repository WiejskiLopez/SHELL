from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition.events.graph_definition_created_event import (
    GraphDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime


class GraphDefinition(AggregateRoot[GraphDefinitionId]):
    __slots__ = ()

    def __init__(
        self,
        id: GraphDefinitionId,
    ) -> None:
        super().__init__(id)

    @classmethod
    def restore(
        cls,
        id: GraphDefinitionId,
    ) -> GraphDefinition:
        return cls(id=id)

    @classmethod
    def create(
        cls,
        id: GraphDefinitionId,
        now: datetime | None = None,
    ) -> GraphDefinition:
        instance = cls(id=id)

        if now is not None:
            instance.append_event(
                GraphDefinitionCreatedEvent.now(
                    graph_definition_id=id,
                    now=CreatedAt.from_datetime(now),
                )
            )

        return instance
