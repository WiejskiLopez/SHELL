"""_assert_task_graph_yaml_exists.py
Responsible for one thing: raising FileNotFoundError when the task graph YAML file is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_task_graph_yaml_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_validate_task] Task graph YAML not found: {path}")
