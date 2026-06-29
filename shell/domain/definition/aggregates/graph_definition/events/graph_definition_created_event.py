from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.value_objects.graph_name import GraphName
    from shell.domain.definition.value_objects.purpose import Purpose


@dataclass(frozen=True, slots=True)
class GraphDefinitionCreatedEvent(DomainEvent):
    graph_definition_id: GraphDefinitionId
    name: GraphName
    purpose: Purpose

    @classmethod
    def now(
        cls,
        graph_definition_id: GraphDefinitionId,
        name: GraphName,
        purpose: Purpose,
        now: CreatedAt,
    ) -> GraphDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            graph_definition_id=graph_definition_id,
            name=name,
            purpose=purpose,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
            GraphDefinitionId,
        )
        from shell.domain.definition.value_objects.graph_name import GraphName
        from shell.domain.definition.value_objects.purpose import Purpose

        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            graph_definition_id=GraphDefinitionId(payload.get("graph_definition_id", "")),
            name=GraphName(payload.get("name", "")),
            purpose=Purpose(payload.get("purpose", "")),
        )
