from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphExecutionSubGraphSettledEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId

    @classmethod
    def now(
        cls,
        parent_graph_execution_id: GraphExecutionId,
        now: datetime,
    ) -> GraphExecutionSubGraphSettledEvent:
        return cls(
            occurred_at=now,
            parent_graph_execution_id=parent_graph_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, object], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            parent_graph_execution_id=GraphExecutionId(payload.get("parent_graph_execution_id")),
        )
