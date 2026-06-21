from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.value_objects.ids import GraphNodeExecutionId


class ConditionEvaluator(Protocol):
    def evaluate(
        self,
        expression: str,
        language: str | None,
        graph_execution: GraphExecution,
        source_node_execution_id: GraphNodeExecutionId,
    ) -> bool: ...
