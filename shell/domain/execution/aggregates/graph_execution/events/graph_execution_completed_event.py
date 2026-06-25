from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import GraphExecutionId
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphExecutionCompletedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    verifier_result: StateData | None = None

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        now: datetime,
        verifier_result: StateData | None = None,
    ) -> GraphExecutionCompletedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            verifier_result=verifier_result,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, object], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_execution_id=GraphExecutionId(payload.get("graph_execution_id")),
            verifier_result=StateData(payload["verifier_result"]) if "verifier_result" in payload and payload["verifier_result"] is not None else None,
        )
