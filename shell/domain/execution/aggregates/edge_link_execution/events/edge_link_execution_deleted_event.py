from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
        EdgeLinkExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True)
class EdgeLinkExecutionDeletedEvent(DomainEvent):
    edge_link_execution_id: EdgeLinkExecutionId

    @classmethod
    def now(
        cls,
        edge_link_execution_id: EdgeLinkExecutionId,
        now: CreatedAt,
    ) -> EdgeLinkExecutionDeletedEvent:
        return cls(
            occurred_at=now,
            edge_link_execution_id=edge_link_execution_id,
        )
