from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.value_objects.node_definition_execution_slot import (
    NodeDefinitionExecutionSlot,
)
from shell.domain.execution.value_objects.node_definition_id import NodeDefinitionId
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class GraphExecutionReadyEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    node_definition_executions: tuple[NodeDefinitionExecutionSlot, ...] = field(
        default_factory=tuple
    )

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        node_definition_executions: list[NodeDefinitionExecutionSlot],
        now: CreatedAt,
    ) -> GraphExecutionReadyEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            node_definition_executions=tuple(node_definition_executions),
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        slots_data = payload.get("node_definition_executions", [])
        if isinstance(slots_data, list):
            slots = tuple(
                NodeDefinitionExecutionSlot(
                    node_definition_id=NodeDefinitionId(s["node_definition_id"]),
                    node_execution_id=NodeExecutionId(s["node_execution_id"])
                    if s.get("node_execution_id")
                    else None,
                )
                for s in slots_data
            )
        else:
            slots = ()
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            node_definition_executions=slots,
        )
