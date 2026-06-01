
from __future__ import annotations

from shell.utils.path.path import PathType




def _assert_task_files_exist(task_dir: PathType, task_files: list) -> None:
    if not task_files:
        raise FileNotFoundError(f"No *.md files found in task_dir: {task_dir}")
