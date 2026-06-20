from __future__ import annotations

from typing import Protocol


class GraphNodeExecutionWorkspace(Protocol):
    async def prepare(self, graph_node_execution_id: str, work_dir: str) -> str: ...
    async def cleanup(self, workspace_path: str) -> None: ...
