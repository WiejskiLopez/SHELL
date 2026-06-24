from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from shell.domain.execution.aggregates.graph_node_execution.services.route_to_error_handler_decision import (
    RouteToErrorHandlerDecision,
)
from shell.domain.execution.services.graph_node_execution_policy.abort_decision import (
    AbortDecision,
)
from shell.domain.execution.services.graph_node_execution_policy.continue_decision import (
    ContinueDecision,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.workflow import Workflow

PolicyDecision = AbortDecision | ContinueDecision | RouteToErrorHandlerDecision


class GraphNodeExecutionPolicy(Protocol):
    """Decides what to do after a node has failed."""

    def decide_after_failure(
        self,
        workflow: Workflow,
        failed_node_execution_id: GraphNodeExecutionId,
        reason: str,
    ) -> PolicyDecision:
        """Return AbortDecision or ContinueDecision."""
        ...
