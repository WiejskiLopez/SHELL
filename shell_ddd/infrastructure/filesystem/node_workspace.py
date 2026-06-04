"""NodeWorkspaceFs — filesystem implementation of the NodeWorkspace port."""
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


class NodeWorkspaceFs:
    """Creates and manages the .node/ workspace directory for a single node execution.

    Directory layout (matching legacy SHELL conventions):
    ``<workspace_path>/.node/{input,output,logs,temp,prompt,scripts,status,port,archive}/``
    """

    async def prepare(self, node_id: str, work_dir: str) -> str:
        """Create workspace directory tree and return the workspace path."""
        ws = Path(work_dir) / node_id
        dot_node = ws / _DOT_NODE
        for subdir in _NODE_SUBDIRS:
            (dot_node / subdir).mkdir(parents=True, exist_ok=True)
        return str(ws)

    async def cleanup(self, workspace_path: str) -> None:
        """Remove the workspace directory tree (best-effort)."""
        ws = Path(workspace_path)
        if ws.exists():
            shutil.rmtree(ws, ignore_errors=True)

    async def read_input(self, workspace_path: str) -> str:
        """Read content of .node/input/input.txt if it exists."""
        p = Path(workspace_path) / _DOT_NODE / "input" / "input.txt"
        if p.exists():
            return p.read_text(encoding="utf-8")
        return ""

    async def write_output(self, workspace_path: str, name: str, body: str) -> Path:
        """Write body to .node/output/<name> and return the path."""
        out = Path(workspace_path) / _DOT_NODE / "output" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        return out
