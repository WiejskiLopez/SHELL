from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.services.node_execution_policy.abort_decision import (
    AbortDecision,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.services.node_execution_policy.node_execution_policy import (
        PolicyDecision,  # noqa: TC002 — PolicyDecision używany jako typ zwracany w decide_after_failure()
    )


class FailFastNodeExecutionPolicy:
    """Default policy — stop the workflow immediately on the first failure."""

    def decide_after_failure(
        self,
        workflow: Workflow,
        failed_node_execution_id: NodeExecutionId,
        reason: str,
    ) -> PolicyDecision:
        return AbortDecision(reason=reason)
