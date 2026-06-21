from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.services.graph_node_execution_policy.policy_action import (
    PolicyAction,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import GraphNodeExecutionId


@dataclass(frozen=True, slots=True)
class RouteToErrorHandlerDecision(PolicyAction):
    target_node_execution_id: GraphNodeExecutionId
    reason: str = ""
