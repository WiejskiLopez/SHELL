from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.value_objects.graph_execution_status import (
        GraphExecutionStatus,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class GraphExecutionUpdatedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    previous_status: GraphExecutionStatus | None = None
    new_status: GraphExecutionStatus | None = None

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        now: CreatedAt,
        previous_status: GraphExecutionStatus | None = None,
        new_status: GraphExecutionStatus | None = None,
    ) -> GraphExecutionUpdatedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            previous_status=previous_status,
            new_status=new_status,
        )
