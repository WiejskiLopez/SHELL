from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.graph_node_definition_execution_slot import (
    GraphNodeDefinitionExecutionSlot,
)
from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphExecutionReadyEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    graph_node_definition_executions: tuple[GraphNodeDefinitionExecutionSlot, ...] = field(default_factory=tuple)

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        graph_node_definition_executions: list[GraphNodeDefinitionExecutionSlot],
        now: datetime,
    ) -> GraphExecutionReadyEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            graph_node_definition_executions=tuple(graph_node_definition_executions),
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        slots_data = payload.get("graph_node_definition_executions", [])
        if isinstance(slots_data, list):
            slots = tuple(
                GraphNodeDefinitionExecutionSlot(
                    graph_node_definition_id=GraphNodeDefinitionId(s["graph_node_definition_id"]),
                    graph_node_execution_id=GraphNodeExecutionId(s["graph_node_execution_id"]) if s.get("graph_node_execution_id") else None,
                )
                for s in slots_data
            )
        else:
            slots = ()
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            graph_node_definition_executions=slots,
        )
