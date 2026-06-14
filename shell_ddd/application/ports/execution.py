from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.execution_result import ExecutionResult
    from shell_ddd.domain.value_objects.manifest import Manifest


class NodeWorkspace(Protocol):
    async def prepare(self, node_id: str, work_dir: str) -> str: ...
    async def cleanup(self, workspace_path: str) -> None: ...


class NodeProcessRunner(Protocol):
    async def run(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult: ...
