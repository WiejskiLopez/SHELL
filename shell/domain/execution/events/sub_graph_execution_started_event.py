from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
)


@dataclass(frozen=True, slots=True)
class SubGraphExecutionStartedEvent(DomainEvent):
    sub_graph_execution_id: GraphExecutionId
    parent_graph_execution_id: GraphExecutionId

    @classmethod
    def now(
        cls,
        sub_graph_execution_id: GraphExecutionId,
        parent_graph_execution_id: GraphExecutionId,
        now: datetime,
    ) -> SubGraphExecutionStartedEvent:
        return cls(
            occurred_at=now,
            sub_graph_execution_id=sub_graph_execution_id,
            parent_graph_execution_id=parent_graph_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            sub_graph_execution_id=GraphExecutionId(payload["sub_graph_execution_id"]),
            parent_graph_execution_id=GraphExecutionId(payload["parent_graph_execution_id"]),
        )
