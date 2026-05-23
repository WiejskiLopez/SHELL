from shell.utils.path.path import PathType
"""Tests for execute/runner modules:
execute_clean, execute_help, execute_version, app properties.
"""

import logging
import pytest
import yaml

from shell.app.app import App
from shell.component.manifest.manifest import Manifest


def _null_logger():
    logger = logging.getLogger("test-task-null")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


# ---------------------------------------------------------------------------
# init_tasker
# ---------------------------------------------------------------------------

def test_init_tasker_copies_files_and_initializes_graph(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "my-task.md").write_text("# my-task\nsome task description", encoding="utf-8")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    graph_yaml = (
        "graph:\n"
        "  - node_name: agent-01\n"
        f"    parent_node_dir: {workspace_dir}\n"
        f"    runner_root_dir: {workspace_dir}\n"
        "    mode: agent\n"
        "    role: developer\n"
        "    type: agent\n"
        "    status: null\n"
    )
    (source_dir / "my-task.yaml").write_text(graph_yaml, encoding="utf-8")

    node_dir = tmp_path / "tasker-node"
    node_dir.mkdir()

    app = App(logger=_null_logger())
    app.app_node_.node_._node_dir = str(node_dir)
    app.app_config_.cli_.cli_properties_._task_name = "my-task"
    app.app_config_.cli_.cli_properties_._source_dir = str(source_dir)

    app.runner_.tasker_.init_tasker()

    task_dir = node_dir / ".node" / "task"
    assert (task_dir / "my-task.md").is_file()
    assert (task_dir / "graph_my-task.yaml").is_file()
    assert len(app.runner_.tasker_.graph_._graph_nodes) == 1



