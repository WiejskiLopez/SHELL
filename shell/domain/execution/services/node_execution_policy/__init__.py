"""NodeExecutionPolicy — decides what to do after a single node finishes."""

from __future__ import annotations

from shell.domain.execution.aggregates.node_execution.services.route_to_error_handler_decision import (
    RouteToErrorHandlerDecision,
)
from shell.domain.execution.services.node_execution_policy.abort_decision import (
    AbortDecision,
)
from shell.domain.execution.services.node_execution_policy.continue_decision import (
    ContinueDecision,
)
from shell.domain.execution.services.node_execution_policy.fail_fast_node_execution_policy import (
    FailFastNodeExecutionPolicy,
)
from shell.domain.execution.services.node_execution_policy.node_execution_policy import (
    NodeExecutionPolicy,
    PolicyDecision,
)
from shell.domain.execution.services.node_execution_policy.policy_action import (
    PolicyAction,
)

__all__ = [
    "AbortDecision",
    "ContinueDecision",
    "FailFastNodeExecutionPolicy",
    "NodeExecutionPolicy",
    "PolicyAction",
    "PolicyDecision",
    "RouteToErrorHandlerDecision",
]
