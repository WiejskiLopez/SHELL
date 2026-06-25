from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.value_objects.graph_definition_id import GraphDefinitionId
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphExecutionSubGraphSpawnRequestedEvent(DomainEvent):
    parent_graph_execution_id: GraphExecutionId
    child_graph_execution_id: GraphExecutionId
    graph_definition_id: GraphDefinitionId
    state_input: StateData | None = None
    correlation_id: str = ""

    @classmethod
    def now(
        cls,
        parent_graph_execution_id: GraphExecutionId,
        child_graph_execution_id: GraphExecutionId,
        graph_definition_id: GraphDefinitionId,
        now: datetime,
        state_input: StateData | None = None,
        correlation_id: str = "",
    ) -> GraphExecutionSubGraphSpawnRequestedEvent:
        return cls(
            occurred_at=now,
            parent_graph_execution_id=parent_graph_execution_id,
            child_graph_execution_id=child_graph_execution_id,
            graph_definition_id=graph_definition_id,
            state_input=state_input,
            correlation_id=correlation_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, object], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            parent_graph_execution_id=GraphExecutionId(payload.get("parent_graph_execution_id")),
            child_graph_execution_id=GraphExecutionId(payload.get("child_graph_execution_id")),
            graph_definition_id=GraphDefinitionId(payload.get("graph_definition_id", "")),
            state_input=StateData(payload["state_input"]) if "state_input" in payload and payload["state_input"] is not None else None,
            correlation_id=payload.get("correlation_id", ""),
        )
