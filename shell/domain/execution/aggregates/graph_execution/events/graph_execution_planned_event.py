from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.platform.value_objects.state_data import StateData


@dataclass(frozen=True, slots=True)
class GraphExecutionPlannedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    plan: StateData | None = None

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        now: CreatedAt,
        plan: StateData | None = None,
    ) -> GraphExecutionPlannedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            plan=plan,
        )
