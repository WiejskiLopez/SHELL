from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class EdgeExecutionDeletedEvent(DomainEvent):
    edge_execution_id: EdgeExecutionId

    @classmethod
    def now(
        cls,
        edge_execution_id: EdgeExecutionId,
        now: CreatedAt,
    ) -> EdgeExecutionDeletedEvent:
        return cls(
            occurred_at=now,
            edge_execution_id=edge_execution_id,
        )
