from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.value_objects.transition_type import TransitionType

if TYPE_CHECKING:
    from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    GraphNodeTransitionExecutionId
)


@dataclass(slots=True)
class GraphNodeTransitionExecution:
    id: GraphNodeTransitionExecutionId
    graph_execution_id: GraphExecutionId
    source_node_execution_id: GraphNodeExecutionId | None
    target_node_execution_id: GraphNodeExecutionId
    transition_type: TransitionType
    priority: int = 0
    condition_expression: str | None = None
    condition_language: str | None = None
    join_wait_count: int | None = None
    max_loop_count: int = 0
    timeout_seconds: int | None = None
    retry_count: int = 0
    retry_delay_seconds: int = 0
    data_mapping: dict[str, str] | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if self.transition_type == TransitionType.CONDITIONAL and not self.condition_expression:
            raise ValueError("CONDITIONAL transition requires condition_expression")
        if self.join_wait_count is not None and self.join_wait_count < 1:
            raise ValueError("join_wait_count must be >= 1")
