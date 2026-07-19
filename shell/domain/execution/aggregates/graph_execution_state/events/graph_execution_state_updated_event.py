from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class GraphExecutionStateUpdatedEvent(DomainEvent):
    graph_execution_state_id: GraphExecutionStateId

    @classmethod
    def now(
        cls,
        graph_execution_state_id: GraphExecutionStateId,
        now: OccurredAt,
    ) -> GraphExecutionStateUpdatedEvent:
        return cls(occurred_at=now, graph_execution_state_id=graph_execution_state_id)
