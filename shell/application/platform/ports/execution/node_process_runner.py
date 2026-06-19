from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.value_objects.execution_result import ExecutionResult
    from shell.domain.execution.value_objects.manifest import Manifest


class NodeProcessRunner(Protocol):
    async def run(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult: ...
