from __future__ import annotations


class FakeNodeExecutionWorkspace:
    async def prepare(self, node_execution_id: str, work_dir: str) -> str:
        return f"/fake/workspace/{node_execution_id}"

    async def cleanup(self, workspace_path: str) -> None:
        pass
