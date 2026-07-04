"""NodeExecutionOutputInterpreter — decides next action based on node execution output.

Enterprise pattern: each node type can have its own interpreter registered.
Sub-graph spawning is now handled by PLANNER nodes, not by NodeExecutionOutputInterpreter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.node_execution.node_execution import (
        NodeExecution,
    )
    from shell.domain.execution.aggregates.workflow import Workflow


@dataclass(frozen=True, slots=True)
class OutputDecision:
    """Decision returned by an NodeExecutionOutputInterpreter.

    Attributes:
        action: One of "advance", "finish", "replan"
        payload: Additional data for the action
    """

    action: str
    payload: dict[str, Any] | None = None

    @classmethod
    def advance(cls) -> OutputDecision:
        return cls("advance")

    @classmethod
    def finish(cls) -> OutputDecision:
        return cls("finish")

    @classmethod
    def replan(cls, payload: dict[str, Any] | None = None) -> OutputDecision:
        return cls("replan", payload=payload)


class NodeExecutionOutputInterpreter(Protocol):
    """Interprets a node's output and returns a decision.

    Implementations are registered per node mode or globally.
    Returns OutputDecision.advance() by default.
    Sub-graph spawning is handled by PLANNER nodes.
    """

    async def interpret(
        self,
        workflow: Workflow,
        graph_execution: GraphExecution,
        node: NodeExecution,
        output_payload: dict[str, Any] | None,
    ) -> OutputDecision: ...
