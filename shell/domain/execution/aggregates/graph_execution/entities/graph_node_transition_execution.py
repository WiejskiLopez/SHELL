from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.value_objects.edge_type import EdgeType

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution.value_objects.ids.graph_node_transition_execution_id import (
        GraphNodeTransitionExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import (
        GraphNodeExecutionId,
    )


@dataclass(slots=True)
class GraphNodeTransitionExecution:
    id: GraphNodeTransitionExecutionId
    graph_execution_id: GraphExecutionId
    source_node_execution_id: GraphNodeExecutionId | None
    target_node_execution_id: GraphNodeExecutionId
    transition_type: EdgeType
    priority: int = 0
    condition_expression: str | None = None
    condition_language: str | None = None
    max_loop_count: int = 0
    timeout_seconds: int | None = None
    retry_count: int = 0
    retry_delay_seconds: int = 0
    data_mapping: dict[str, str] | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if self.transition_type == EdgeType.CONDITIONAL and not self.condition_expression:
            raise ValueError("CONDITIONAL transition requires condition_expression")
