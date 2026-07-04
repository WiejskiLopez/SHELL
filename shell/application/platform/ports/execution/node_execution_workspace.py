from __future__ import annotations

from typing import Protocol


class NodeExecutionWorkspace(Protocol):
    async def prepare(self, node_execution_id: str, work_dir: str) -> str: ...
    async def cleanup(self, workspace_path: str) -> None: ...
