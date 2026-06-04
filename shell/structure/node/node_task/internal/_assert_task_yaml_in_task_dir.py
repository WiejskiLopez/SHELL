from __future__ import annotations

from shell.utils.path.path import PathType



def _assert_task_yaml_in_task_dir(yaml_files: list, task_dir: PathType) -> None:
    if not yaml_files:
        raise FileNotFoundError(f"[NodeTask] no .yaml file found in task_dir: {task_dir}")
