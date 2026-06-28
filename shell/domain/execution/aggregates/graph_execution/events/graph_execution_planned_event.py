from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphExecutionPlannedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    plan: StateData | None = None

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        now: datetime,
        plan: StateData | None = None,
    ) -> GraphExecutionPlannedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            plan=plan,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, object], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            plan=StateData(payload["plan"]) if "plan" in payload and payload["plan"] is not None else None,
        )
