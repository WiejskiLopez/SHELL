from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.value_objects.reason import Reason
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphExecutionFailedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    reason: Reason | None = None

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        now: datetime,
        reason: Reason | None = None,
    ) -> GraphExecutionFailedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            reason=reason,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            reason=Reason(payload.get("reason", "")) if payload["reason"] else None,
        )
