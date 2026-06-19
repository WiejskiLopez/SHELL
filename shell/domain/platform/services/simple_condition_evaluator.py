from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.platform.value_objects.ids import GraphNodeExecutionId


class SimpleConditionEvaluator:
    def evaluate(
        self,
        expression: str,
        language: str | None,
        graph_execution: GraphExecution,
        source_node_execution_id: GraphNodeExecutionId,
    ) -> bool:
        if language and language.lower() != "plain":
            return False

        expr = expression.strip().lower()
        if expr in ("true", "yes", "1"):
            return True
        if expr in ("false", "no", "0"):
            return False

        return bool(expression)
