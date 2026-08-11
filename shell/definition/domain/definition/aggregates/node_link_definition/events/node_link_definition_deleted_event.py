from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.definition.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
        NodeLinkDefinitionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class NodeLinkDefinitionDeletedEvent(DomainEvent):
    node_link_definition_id: NodeLinkDefinitionId

    @classmethod
    def now(
        cls, node_link_definition_id: NodeLinkDefinitionId, now: OccurredAt
    ) -> NodeLinkDefinitionDeletedEvent:
        return cls(occurred_at=now, node_link_definition_id=node_link_definition_id)
