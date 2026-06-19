from __future__ import annotations

from dataclasses import dataclass

from shell.domain.execution.services.graph_node_execution_policy.policy_action import (
    PolicyAction,
)


@dataclass(frozen=True, slots=True)
class AbortDecision(PolicyAction):
    """Signal: stop the workflow and mark it as failed."""

    reason: str = ""
