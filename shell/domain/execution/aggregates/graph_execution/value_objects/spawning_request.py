from __future__ import annotations

from dataclasses import dataclass

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class SpawningRequest(ValueObject):
    child_graph_execution_id: GraphExecutionId
    expected_node_count: int
    initialized_node_count: int
    definition_id: str
    correlation_id: str
