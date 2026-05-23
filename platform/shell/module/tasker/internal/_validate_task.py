"""_validate_task.py
Responsible for one thing: asserting that all required task files exist.
"""

from __future__ import annotations

from shell.module.tasker.internal._assert_task_md_exists import _assert_task_md_exists
from shell.module.tasker.internal._assert_task_graph_yaml_exists import _assert_task_graph_yaml_exists
from shell.constants.constants import DOT_NODE, DIR_TASK


def _validate_task(app) -> None:
    """Assert that all required task files exist."""
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    task_name = app.cli_.cli_properties_.task_name_
    _assert_task_graph_yaml_exists(task_dir / f"{task_name}.yaml")
    _assert_task_md_exists(task_dir / f"{task_name}.md")
