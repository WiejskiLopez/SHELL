from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell.application.platform.ports.ports import NodeExecutionProcessRunner
    from shell.domain.execution.value_objects.execution_result import ExecutionResult


class _BaseStrategy:
    """Shared logic: build argv, call runner, return result."""

    mode: str  # overridden by subclasses

    async def execute(
        self,
        node_execution_id: str,
        workspace_path: str,
        runner: NodeExecutionProcessRunner,
    ) -> ExecutionResult:
        manifest = Manifest(
            name=node_execution_id,
            mode=Mode(self.mode),
            role=self.mode,
            node_type=self.mode,
            version="1",
        )
        return await runner.run(manifest, workspace_path)
