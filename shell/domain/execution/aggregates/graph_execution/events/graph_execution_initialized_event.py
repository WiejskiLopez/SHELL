from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.value_objects.graph_definition_id import GraphDefinitionIdRef
from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class GraphExecutionInitializedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    task_execution_id: TaskExecutionId
    graph_definition_id: GraphDefinitionIdRef
    graph_node_definition_ids: tuple[GraphNodeDefinitionId, ...]

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: GraphDefinitionIdRef,
        graph_node_definition_ids: list[GraphNodeDefinitionId],
        now: CreatedAt,
    ) -> GraphExecutionInitializedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition_id,
            graph_node_definition_ids=tuple(graph_node_definition_ids),
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            graph_definition_id=GraphDefinitionIdRef(payload["graph_definition_id"]),
            graph_node_definition_ids=tuple(
                GraphNodeDefinitionId(nid) for nid in payload.get("graph_node_definition_ids", [])
            ),
        )
