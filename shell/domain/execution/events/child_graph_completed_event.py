from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.execution.value_objects.ids import GraphExecutionId


@dataclass(frozen=True, slots=True)
class ChildGraphCompletedEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId
    child_graph_execution_id: GraphExecutionId
    status: str  # "done" or "failed"
    result: dict[str, Any] | None = None
    error: str = ""

    @classmethod
    def now(
        cls,
        parent_graph_execution_id: GraphExecutionId,
        child_graph_execution_id: GraphExecutionId,
        status: str,
        result: dict[str, Any] | None = None,
        error: str = "",
        now: datetime | None = None,
    ) -> ChildGraphCompletedEvent:
        from datetime import datetime as dt

        return cls(
            occurred_at=now or dt.now(),
            parent_graph_execution_id=parent_graph_execution_id,
            child_graph_execution_id=child_graph_execution_id,
            status=status,
            result=result,
            error=error,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            parent_graph_execution_id=GraphExecutionId(payload["parent_graph_execution_id"]),
            child_graph_execution_id=GraphExecutionId(payload["child_graph_execution_id"]),
            status=payload.get("status", "done"),
            result=payload.get("result"),
            error=payload.get("error", ""),
        )
