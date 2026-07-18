from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class GraphExecutionUpdatedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        now: CreatedAt,
    ) -> GraphExecutionUpdatedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
        )
