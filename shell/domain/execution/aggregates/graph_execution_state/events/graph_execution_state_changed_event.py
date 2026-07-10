from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.state_key import (
        StateKey,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.state_direction import StateDirection


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphExecutionStateChangedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    graph_execution_state_id: GraphExecutionStateId
    direction: StateDirection
    key: StateKey
    old_value: object | None
    new_value: object | None

    @classmethod
    def now(
        cls,
        *,
        graph_execution_id: GraphExecutionId,
        graph_execution_state_id: GraphExecutionStateId,
        direction: StateDirection,
        key: StateKey,
        old_value: object | None,
        new_value: object | None,
        now: CreatedAt,
    ) -> GraphExecutionStateChangedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            graph_execution_state_id=graph_execution_state_id,
            direction=direction,
            key=key,
            old_value=old_value,
            new_value=new_value,
        )
