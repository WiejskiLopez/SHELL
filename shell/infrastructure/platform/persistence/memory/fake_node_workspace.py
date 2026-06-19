from __future__ import annotations


class FakeNodeWorkspace:
    async def prepare(self, graph_node_execution_id: str, work_dir: str) -> str:
        return f"/fake/workspace/{graph_node_execution_id}"

    async def cleanup(self, workspace_path: str) -> None:
        pass
