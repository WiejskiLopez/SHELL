from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from shell.application.platform.ports.ports import NodeExecutionProcessRunner
    from shell.domain.execution.value_objects.execution_result import ExecutionResult


@runtime_checkable
class NodeExecutionStrategy(Protocol):
    """Strategy for executing a node; one implementation per mode."""

    async def execute(
        self,
        node_execution_id: str,
        workspace_path: str,
        runner: NodeExecutionProcessRunner,
    ) -> ExecutionResult: ...
