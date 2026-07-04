"""AgentNodeExecutionOutputInterpreter — default NodeExecutionOutputInterpreter for AGENT-mode nodes.

Sub-graph spawning is now handled by PLANNER nodes, not by AGENT output.
This interpreter simply returns advance for any output.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.services.node_execution_output_interpreter import OutputDecision

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.node_execution.node_execution import (
        NodeExecution,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.platform.ports.log import Logger


class AgentNodeExecutionOutputInterpreter:
    """Default interpreter for AGENT nodes.

    Sub-graph spawning is delegated to PLANNER nodes.
    Always returns advance.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def interpret(
        self,
        workflow: Workflow,
        graph_execution: GraphExecution,
        node: NodeExecution,
        output_payload: dict[str, Any] | None,
    ) -> OutputDecision:
        return OutputDecision.advance()
