from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class GraphExecutionSubGraphSettledEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId

    @classmethod
    def now(
        cls,
        parent_graph_execution_id: GraphExecutionId,
        now: CreatedAt,
    ) -> GraphExecutionSubGraphSettledEvent:
        return cls(
            occurred_at=now,
            parent_graph_execution_id=parent_graph_execution_id,
        )
