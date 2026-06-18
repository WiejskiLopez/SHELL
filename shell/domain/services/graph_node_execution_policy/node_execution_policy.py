from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from shell.domain.services.graph_node_execution_policy.abort_decision import (
    AbortDecision,
)
from shell.domain.services.graph_node_execution_policy.continue_decision import (
    ContinueDecision,
)

if TYPE_CHECKING:
    from shell.domain.aggregates.workflow import Workflow
    from shell.domain.value_objects.ids import GraphNodeExecutionId

PolicyDecision = AbortDecision | ContinueDecision


class NodeExecutionPolicy(Protocol):
    """Decides what to do after a node has failed."""

    def decide_after_failure(
        self,
        workflow: Workflow,
        failed_node_execution_id: GraphNodeExecutionId,
        reason: str,
    ) -> PolicyDecision:
        """Return AbortDecision or ContinueDecision."""
        ...
