"""PlannerResultEvent — emitowany po wykonaniu PLANNER node z poprawnym JSON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.graph_execution_id import GraphExecutionId
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class PlannerResultEvent(DomainEvent):
    graph_node_execution_id: GraphNodeExecutionId
    graph_execution_id: GraphExecutionId
    stage: str
    spawn: tuple[str, ...]
    raw_json: str

    @classmethod
    def now(
        cls,
        graph_node_execution_id: GraphNodeExecutionId,
        graph_execution_id: GraphExecutionId,
        stage: str,
        spawn: tuple[str, ...],
        raw_json: str,
        now: datetime | None = None,
    ) -> PlannerResultEvent:
        from datetime import datetime as dt

        return cls(
            occurred_at=now or dt.now(),
            graph_node_execution_id=graph_node_execution_id,
            graph_execution_id=graph_execution_id,
            stage=stage,
            spawn=spawn,
            raw_json=raw_json,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            stage=payload.get("stage", ""),
            spawn=tuple(payload.get("spawn", [])),
            raw_json=payload.get("raw_json", ""),
        )
