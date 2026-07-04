from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class GraphExecutionSagaStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class GraphExecutionSagaState:
    saga_id: str
    graph_execution_id: str
    expected_nodes_count: int
    node_definition_executions: dict[str, str] = field(default_factory=dict)
    status: GraphExecutionSagaStatus = GraphExecutionSagaStatus.PENDING
    version: int = 1

    def record_node_execution_created(
        self, node_definition_id: str, node_execution_id: str
    ) -> None:
        self.node_definition_executions[node_definition_id] = node_execution_id
        if self.is_complete:
            self.status = GraphExecutionSagaStatus.COMPLETED

    @property
    def is_complete(self) -> bool:
        return len(self.node_definition_executions) >= self.expected_nodes_count
