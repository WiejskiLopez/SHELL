"""Workspace — filesystem implementation of the GraphNodeExecutionWorkspace port."""

from __future__ import annotations

import shutil
from pathlib import Path

# Standard sub-directories inside .node/
_NODE_SUBDIRS = [
    "input",
    "output",
    "logs",
    "temp",
    "prompt",
    "scripts",
    "status",
    "port",
    "archive",
]
_DOT_NODE = ".node"


class Workspace:
    """Creates and manages the .node/ workspace directory for a single node execution.

    Directory layout (matching legacy SHELL conventions):
    ``<workspace_path>/.node/{input,output,logs,temp,prompt,scripts,status,port,archive}/``
    """

    async def prepare(self, graph_node_execution_id: str, work_dir: str) -> str:
        """Create workspace directory tree and return the workspace path."""
        workspace_path = Path(work_dir) / graph_node_execution_id
        dot_node = workspace_path / _DOT_NODE
        for subdir in _NODE_SUBDIRS:
            (dot_node / subdir).mkdir(parents=True, exist_ok=True)
        return str(workspace_path)

    async def cleanup(self, workspace_path: str) -> None:
        """Remove the workspace directory tree (best-effort)."""
        workspace_path_obj = Path(workspace_path)
        if workspace_path_obj.exists():
            shutil.rmtree(workspace_path_obj, ignore_errors=True)

    async def read_input(self, workspace_path: str) -> str:
        """Read content of .node/input/input.txt if it exists."""
        input_path = Path(workspace_path) / _DOT_NODE / "input" / "input.txt"
        if input_path.exists():
            return input_path.read_text(encoding="utf-8")
        return ""

    async def write_output(self, workspace_path: str, name: str, body: str) -> Path:
        """Write body to .node/output/<name> and return the path."""
        out = Path(workspace_path) / _DOT_NODE / "output" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        return out
