"""CommandBuilder — builds subprocess argv per node execution mode."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.manifest import Manifest

# Directory names inside .node/
_DOT_NODE = ".node"
DIR_OUTPUT = "output"
DIR_LOGS = "logs"
DIR_INPUT = "input"
DIR_TEMP = "temp"


def build_agent_command(
    manifest: Manifest,
    workspace_path: str,
    prompt: str = "",
    model: str = "",
    extra_add_dirs: list[str] | None = None,
) -> list[str]:
    """Build argv for running the `copilot` agent binary."""
    import shutil

    binary = shutil.which("copilot")
    if binary is None:
        raise FileNotFoundError(
            "copilot binary not found on PATH. Install GitHub Copilot CLI."
        )

    cmd: list[str] = []

    # On Windows .cmd/.bat wrappers need to be invoked via cmd /c
    import os

    if os.name == "nt" and binary.lower().endswith((".cmd", ".bat")):
        cmd += ["cmd", "/c", binary]
    else:
        cmd.append(binary)

    if model:
        cmd += ["--model", model]

    import pathlib

    ws = pathlib.Path(workspace_path)
    output_dir = ws / _DOT_NODE / DIR_OUTPUT
    logs_dir = ws / _DOT_NODE / DIR_LOGS

    cmd += ["--add-dir", str(output_dir)]
    if extra_add_dirs:
        for d in extra_add_dirs:
            cmd += ["--add-dir", d]
    cmd += ["--add-dir", str(ws)]
    cmd += ["--log-dir", str(logs_dir)]

    return cmd


def build_sub_node_command(
    entrypoint_path: str,
    node_dir: str,
    source_dir: str,
    work_dir: str,
    task_name: str,
    task_dir: str,
    mode: str = "",
    model: str = "",
    role: str = "",
    parent_node_dir: str = "",
    parent_thread_id: str = "",
    python_exe: str | None = None,
) -> list[str]:
    """Build argv for running a sub-node entrypoint (used by tasker)."""
    exe = python_exe or sys.executable
    cmd = [exe, entrypoint_path]
    cmd += ["--node-dir", node_dir]
    cmd += ["--source-dir", source_dir]
    cmd += ["--work-dir", work_dir]
    cmd += ["--task-name", task_name]
    cmd += ["--task-dir", task_dir]
    if parent_node_dir:
        cmd += ["--parent-node-dir", parent_node_dir]
    if parent_thread_id:
        cmd += ["--parent-thread-id", parent_thread_id]
    if mode == "agent" and model:
        cmd += ["--model", model]
    if role:
        cmd += ["--role", role]
    return cmd
