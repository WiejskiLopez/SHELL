from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from shell.domain.execution.services.graph_node_execution_policy.abort_decision import (
    AbortDecision,
)
from shell.domain.execution.services.graph_node_execution_policy.continue_decision import (
    ContinueDecision,
)
from shell.domain.execution.services.graph_node_execution_policy.route_to_error_handler_decision import (
    RouteToErrorHandlerDecision,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.platform.value_objects.ids import GraphNodeExecutionId

PolicyDecision = AbortDecision | ContinueDecision | RouteToErrorHandlerDecision


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
