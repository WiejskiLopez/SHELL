from __future__ import annotations

from dataclasses import dataclass

from shell.domain.services.graph_node_execution_policy.policy_action import (
    PolicyAction,
)


@dataclass(frozen=True, slots=True)
class ContinueDecision(PolicyAction):
    """Signal: continue with the next node despite the failure."""
