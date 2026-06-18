from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.ports.ports import NodeProcessRunner
    from shell.domain.value_objects.execution_result import ExecutionResult


class GraphNodeExecutionStrategy(Protocol):
    """Strategy for executing a node; one implementation per mode."""

    async def execute(
        self,
        graph_node_execution_id: str,
        workspace_path: str,
        runner: NodeProcessRunner,
    ) -> ExecutionResult: ...
