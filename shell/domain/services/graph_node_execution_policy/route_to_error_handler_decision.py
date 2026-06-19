from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.services.graph_node_execution_policy.policy_action import (
    PolicyAction,
)

if TYPE_CHECKING:
    from shell.domain.value_objects.ids import GraphNodeExecutionId


@dataclass(frozen=True, slots=True)
class RouteToErrorHandlerDecision(PolicyAction):
    target_node_execution_id: GraphNodeExecutionId
    reason: str = ""
