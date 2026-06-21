from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.value_objects.ids import GraphExecutionId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class ChildGraphsCompletedEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId
    completed_child_ids: tuple[GraphExecutionId, ...]
    combined_output: dict[str, Any] | None = None

    @classmethod
    def now(
        cls,
        parent_graph_execution_id: GraphExecutionId,
        completed_child_ids: tuple[GraphExecutionId, ...],
        combined_output: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> ChildGraphsCompletedEvent:
        from datetime import datetime as dt

        return cls(
            occurred_at=now or dt.now(),
            parent_graph_execution_id=parent_graph_execution_id,
            completed_child_ids=completed_child_ids,
            combined_output=combined_output,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            parent_graph_execution_id=GraphExecutionId(payload["parent_graph_execution_id"]),
            completed_child_ids=tuple(
                GraphExecutionId(cid) for cid in payload.get("completed_child_ids", [])
            ),
            combined_output=payload.get("combined_output"),
        )
