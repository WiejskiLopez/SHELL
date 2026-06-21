from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.graph_execution_id import GraphExecutionId
    from shell.domain.execution.aggregates.graph_execution_state_input.graph_execution_state_input_id import (
        GraphExecutionStateInputId,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphExecutionStateInputChangedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    graph_execution_state_input_id: GraphExecutionStateInputId
    key: str
    old_value: object | None
    new_value: object | None

    @classmethod
    def now(
        cls,
        *,
        graph_execution_id: GraphExecutionId,
        graph_execution_state_input_id: GraphExecutionStateInputId,
        key: str,
        old_value: object | None,
        new_value: object | None,
        now: datetime,
    ) -> GraphExecutionStateInputChangedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            graph_execution_state_input_id=graph_execution_state_input_id,
            key=key,
            old_value=old_value,
            new_value=new_value,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            graph_execution_id=payload["graph_execution_id"],
            graph_execution_state_input_id=payload["graph_execution_state_input_id"],
            key=payload["key"],
            old_value=payload.get("old_value"),
            new_value=payload.get("new_value"),
            schema_version=schema_version,
        )
