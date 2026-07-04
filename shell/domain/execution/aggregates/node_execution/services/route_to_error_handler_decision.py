from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.services.node_execution_policy.policy_action import (
    PolicyAction,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )


@dataclass(frozen=True, slots=True)
class RouteToErrorHandlerDecision(PolicyAction):
    target_node_execution_id: NodeExecutionId
    reason: str = ""
