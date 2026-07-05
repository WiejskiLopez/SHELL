from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.platform.value_objects.reason import Reason


@dataclass(frozen=True, slots=True)
class GraphExecutionFailedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    reason: Reason | None = None

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        now: CreatedAt,
        reason: Reason | None = None,
    ) -> GraphExecutionFailedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            reason=reason,
        )
