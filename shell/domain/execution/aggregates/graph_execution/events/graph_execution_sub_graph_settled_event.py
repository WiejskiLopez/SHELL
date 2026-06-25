from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphExecutionSubGraphSettledEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId
    child_results: list[StateData] | None = None

    @classmethod
    def now(
        cls,
        parent_graph_execution_id: GraphExecutionId,
        now: datetime,
        child_results: list[StateData] | None = None,
    ) -> GraphExecutionSubGraphSettledEvent:
        return cls(
            occurred_at=now,
            parent_graph_execution_id=parent_graph_execution_id,
            child_results=child_results or [],
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, object], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            parent_graph_execution_id=GraphExecutionId(payload.get("parent_graph_execution_id")),
            child_results=[StateData(r) for r in payload.get("child_results", [])] if payload.get("child_results") is not None else None,
        )
