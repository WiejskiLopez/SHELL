from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.services.graph_node_execution_policy.abort_decision import (
    AbortDecision,
)
from shell.domain.execution.services.graph_node_execution_policy.graph_node_execution_policy import (
    PolicyDecision,  # noqa: TC002 — PolicyDecision używany jako typ zwracany w decide_after_failure()
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import GraphNodeExecutionId


class FailFastGraphNodeExecutionPolicy:
    """Default policy — stop the workflow immediately on the first failure."""

    def decide_after_failure(
        self,
        workflow: Workflow,
        failed_node_execution_id: GraphNodeExecutionId,
        reason: str,
    ) -> PolicyDecision:
        return AbortDecision(reason=reason)
