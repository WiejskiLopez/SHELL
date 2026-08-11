from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.definition.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class NodeDefinitionCreatedEvent(DomainEvent):
    node_definition_id: NodeDefinitionId

    @classmethod
    def now(
        cls,
        node_definition_id: NodeDefinitionId,
        now: OccurredAt,
    ) -> NodeDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            node_definition_id=node_definition_id,
        )
