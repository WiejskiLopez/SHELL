from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.ports.ports import GraphNodeExecutionProcessRunner
    from shell.domain.execution.value_objects.execution_result import ExecutionResult


class _BaseStrategy:
    """Shared logic: build argv, call runner, return result."""

    mode: str  # overridden by subclasses

    async def execute(
        self,
        graph_node_execution_id: str,
        workspace_path: str,
        runner: GraphNodeExecutionProcessRunner,
    ) -> ExecutionResult:
        from shell.domain.execution.value_objects.manifest import Manifest

        manifest = Manifest(
            name=graph_node_execution_id,
            mode=self.mode,
            role=self.mode,
            node_type=self.mode,
            version="1",
        )
        return await runner.run(manifest, workspace_path)
