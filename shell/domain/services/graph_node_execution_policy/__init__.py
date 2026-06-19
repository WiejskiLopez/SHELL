"""NodeExecutionPolicy — decides what to do after a single node finishes."""
from __future__ import annotations


from shell.domain.services.graph_node_execution_policy.abort_decision import (
    AbortDecision,
)
from shell.domain.services.graph_node_execution_policy.continue_decision import (
    ContinueDecision,
)
from shell.domain.services.graph_node_execution_policy.fail_fast_policy import (
    FailFastPolicy,
)
from shell.domain.services.graph_node_execution_policy.node_execution_policy import (
    NodeExecutionPolicy,
    PolicyDecision,
)
from shell.domain.services.graph_node_execution_policy.policy_action import (
    PolicyAction,
)

__all__ = [
    "AbortDecision",
    "ContinueDecision",
    "FailFastPolicy",
    "NodeExecutionPolicy",
    "PolicyAction",
    "PolicyDecision",
]
