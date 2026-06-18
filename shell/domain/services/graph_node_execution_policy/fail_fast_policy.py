from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.services.graph_node_execution_policy.abort_decision import (
    AbortDecision,
)
from shell.domain.services.graph_node_execution_policy.node_execution_policy import (
    PolicyDecision,
)

if TYPE_CHECKING:
    from shell.domain.aggregates.workflow import Workflow
    from shell.domain.value_objects.ids import GraphNodeExecutionId


class FailFastPolicy:
    """Default policy — stop the workflow immediately on the first failure."""

    def decide_after_failure(
        self,
        workflow: Workflow,
        failed_node_execution_id: GraphNodeExecutionId,
        reason: str,
    ) -> PolicyDecision:
        return AbortDecision(reason=reason)
